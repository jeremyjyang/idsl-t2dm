#!/usr/bin/env python3
"""
Utility functions for the PubChem PUG REST API.

 see: http://pubchem.ncbi.nlm.nih.gov/rest/pug/
 URL paths:
	<domain>/<namespace>/<identifiers>

  compound domain:
	compound/cid 
 	compound/name 
 	compound/smiles 
 	compound/inchi 
 	compound/inchikey 
 	compound/listkey
 	compound/substructure/{smiles|inchi}

  substance domain:
	substance/sid 
 	substance/name 
 	substance/listkey
 	substance/sourceid/<source name> 
 	substance/sourceall/<source name> 
     substance/sid/<SID>/cids/JSON
     substance/sid/<SID>/cids/XML?cids_type=all

  assay domain:
	assay/aid 
 	assay/listkey 
 	assay/type/{all|confirmatory|doseresponse|onhold|panel|rnai|screening|summary}
 	assay/sourceall/<source name>

  sources domain:
	sources/{substance|assay}

  <identifiers> = comma-separated list of positive integers (cid, sid, aid) or
  identifier strings (source, inchikey, listkey); single identifier string
  (name, smiles; inchi by POST only)
"""
import sys,os,re,types,math,time
import csv,json
import urllib,urllib.request,urllib.parse
import xml.dom.minidom #replace with ETree
#
import rest_utils
import time_utils
#
OFMTS={
	'XML':'application/xml',
	'JSON':'application/json',
	'JSONP':'application/javascript',
	'ASNB':'application/ber-encoded',
	'SDF':'application/x-mdl-sdfile',
	'CSV':'text/csv',
	'PNG':'image/png',
	'TXT':'text/plain'
	}
#
OUTCOME_CODES = {'inactive':1,'active':2,'inconclusive':3,'unspecified':4,'probe':5}
#
#############################################################################
def ListSubstanceSources(base_url,fout,verbose):
  rval=rest_utils.GetURL(base_url+'/sources/substance/JSON',parse_json=True,verbose=verbose)
  #print(json.dumps(rval,indent=2), file=sys.stderr)
  sources = rval['InformationList']['SourceName']
  n_src=0;
  for source in sorted(sources):
    fout.write('"%s"\n'%source)
    n_src+=1
  print('n_src: %d'%n_src, file=sys.stderr)
  return

#############################################################################
def ListAssaySources(base_url,fout,verbose):
  rval=rest_utils.GetURL(base_url+'/sources/assay/JSON',parse_json=True,verbose=verbose)
  #print(json.dumps(rval,indent=2), file=sys.stderr)
  sources = rval['InformationList']['SourceName']
  n_src=0;
  for source in sorted(sources):
    fout.write('"%s"\n'%source)
    n_src+=1
  print('n_src: %d'%n_src, file=sys.stderr)
  return

##############################################################################
def Cid2Sdf(base_url,id_query,verbose=0):
  url=(base_url+'/compound/cid/%d/SDF'%id_query)
  if verbose>2: print('URL: %s'%url, file=sys.stderr)
  txt=rest_utils.GetURL(url,verbose=verbose)
  return txt

#############################################################################
def Cid2Smiles(base_url,id_query,verbose=0):
  url=(base_url+'/compound/cid/%d/property/IsomericSMILES/JSON'%id_query)
  if verbose>2: print('URL: %s'%url, file=sys.stderr)
  d=rest_utils.GetURL(url,parse_json=True,verbose=verbose)
  try:
    props = d['PropertyTable']['Properties']
    smi=props[0]['IsomericSMILES']
  except Exception as  e:
    print('Error (Exception): %s'%e, file=sys.stderr)
    #print('DEBUG: d = %s'%str(d), file=sys.stderr)
    smi=None
  return smi

##############################################################################
def Sid2Sdf(base_url,id_query,verbose=0):
  url=(base_url+'/substance/sid/%d/SDF'%id_query)
  if verbose>2: print('URL: %s'%url, file=sys.stderr)
  #txt=rest_utils.GetURL(url,headers={'Accept':'%s'%OFMTS['TXT']},verbose=verbose)
  txt=rest_utils.GetURL(url,verbose=verbose)
  return txt

#############################################################################
def Sid2AssaySummaryCSV(base_url,id_query,verbose=0):
  txt=rest_utils.GetURL(base_url+'/substance/sid/%d/assaysummary/CSV'%id_query,verbose=verbose)
  #print('DEBUG: 1st line: %s'%txt.splitlines()[0], file=sys.stderr)
  return txt

#############################################################################
def Sid2Cid(base_url,sid,verbose=0):
  d=rest_utils.GetURL(base_url+'/substance/sid/%d/cids/JSON?cids_type=standardized'%sid,parse_json=True,verbose=verbose)
  try:
    infos = d['InformationList']['Information']
    cid=infos[0]['CID'][0]
  except Exception as  e:
    print('Error (Exception): %s'%e, file=sys.stderr)
    #print('DEBUG: d = %s'%str(d), file=sys.stderr)
    cid=None
  #print('DEBUG: sid=%s ; cid=%s'%(sid,cid), file=sys.stderr)
  return cid

#############################################################################
def Sid2Smiles(base_url,sid,verbose=0):
  cid = Sid2Cid(base_url,sid,verbose)
  return Cid2Smiles(base_url,cid,verbose)

#############################################################################
def Cid2Sids(base_url,cid,verbose=0):
  d=rest_utils.GetURL(base_url+'/compound/cid/%d/sids/JSON'%cid,parse_json=True,verbose=verbose)
  sids=[]
  try:
    infos = d['InformationList']['Information']
    for info in infos:
      sids.extend(info['SID'])
  except Exception as  e:
    print('Error (Exception): %s'%e, file=sys.stderr)
    #print('DEBUG: d = %s'%str(d), file=sys.stderr)
  return sids

#############################################################################
### JSON returned: "{u'IdentifierList': {u'CID': [245086]}}"
### Problem: must quote forward slash '/' in smiles.  2nd param in quote()
### specifies "safe" chars to not quote, '/' being the default, so specify
### '' for no safe chars.
#############################################################################
def Smi2Ids(base_url,smi,verbose):
  d=rest_utils.GetURL(base_url+'/compound/smiles/%s/cids/JSON'%urllib.parse.quote(smi),parse_json=True,verbose=verbose)
  ids=None
  try:
    ids=d['IdentifierList']
    #print('DEBUG: ids = %s'%str(ids), file=sys.stderr)
  except Exception as  e:
    print('Error (Exception): %s'%e, file=sys.stderr)
  return ids

#############################################################################
def Smi2Cids(base_url,smi,verbose):
  ids = Smi2Ids(base_url,smi,verbose)
  cids=[]
  try:
    cids=ids['CID']
  except Exception as  e:
    print('Error (Exception): %s'%e, file=sys.stderr)
  return cids

#############################################################################
#  sids: '846753,846754,846755,846760,846761,3712736,3712737'
#  cids: '644415,5767160,644417,644418,644420'
#  Very slow -- progress?
#############################################################################
def Sids2Cids(base_url,ids,verbose=0):
  ## Use method POST; put SIDs in data.
  ids_txt='sid='+(','.join(map(lambda x:str(x),ids)))
  #print('DEBUG: ids_txt = %s'%ids_txt, file=sys.stderr)
  req=urllib.request.Request(url=base_url+'/substance/sid/cids/TXT?cids_type=standardized',
	headers={'Accept':OFMTS['TXT'],'Content-type':'application/x-www-form-urlencoded'},
	data=ids_txt
	)
  #print('DEBUG: req.get_method() = %s'%req.get_method(), file=sys.stderr)
  #print('DEBUG: req.has_data() = %s'%req.has_data(), file=sys.stderr)
  f=urllib.request.urlopen(req)
  cids=[]
  while True:
    line=f.readline()
    if not line: break
    try:
      cid=int(line)
      cids.append(cid)
    except:
      pass
  return cids

#############################################################################
def Sids2CidsCSV(base_url,ids,fout,verbose=0):
  t0 = time.time()
  fout.write('sid,cid\n')
  n_in=0; n_out=0; n_err=0;
  for sid in ids:
    n_in+=1
    cid = Sid2Cid(base_url,sid,verbose)
    try:
      cid=int(cid)
    except Exception as  e:
      n_err+=1
      continue
    fout.write('%d,%d\n'%(sid,cid))
    n_out+=1
    if verbose>0 and (n_in%1000)==0:
      print('processed: %6d / %6d (%.1f%%); elapsed time: %s'%(n_in,len(ids), 100.0*n_in/len(ids),time_utils.NiceTime(time.time()-t0)), file=sys.stderr)
  print('sids in: %d'%len(ids), file=sys.stderr)
  print('cids out: %d'%n_out, file=sys.stderr)
  print('errors: %d'%n_err, file=sys.stderr)

#############################################################################
def Cids2SidsCSV(base_url,ids,fout,verbose=0):
  fout.write('cid,sid\n')
  n_out=0; n_err=0;
  for cid in ids:
    try:
      d=rest_utils.GetURL(base_url+'/compound/cid/%s/sids/TXT'%cid,verbose=verbose)
      sids=d.splitlines()
    except Exception as  e:
      print('Error (Exception): %s'%e, file=sys.stderr)
      n_err+=1
      continue
      #print('DEBUG: d = %s'%str(d), file=sys.stderr)
    for sid in sids:
      fout.write('%s,%s\n'%(cid,sid))
      n_out+=1
  print('cids in: %d'%len(ids), file=sys.stderr)
  print('sids out: %d'%n_out, file=sys.stderr)
  print('errors: %d'%n_err, file=sys.stderr)

#############################################################################
def Cids2Assaysummary(base_url,ids,fout,verbose=0):
  n_out=0; n_err=0;
  for cid in ids:
    try:
      d=rest_utils.GetURL(base_url+'/compound/cid/%s/assaysummary/CSV'%cid,verbose=verbose)
      rows=d.splitlines()
    except Exception as  e:
      print('Error (Exception): %s'%e, file=sys.stderr)
      n_err+=1
      continue
    for i,row in enumerate(rows):
      if i==0 and n_out>0: continue #1 header only
      fout.write('%s\n'%(row))
      n_out+=1
  print('cids in: %d'%len(ids), file=sys.stderr)
  print('assay summaries out: %d'%n_out, file=sys.stderr)
  print('errors: %d'%n_err, file=sys.stderr)

#############################################################################
def Sids2Assaysummary(base_url,ids,fout,verbose=0):
  n_out=0; n_err=0;
  for sid in ids:
    try:
      d=rest_utils.GetURL(base_url+'/substance/sid/%s/assaysummary/CSV'%sid,verbose=verbose)
      rows=d.splitlines()
    except Exception as  e:
      print('Error (Exception): %s'%e, file=sys.stderr)
      n_err+=1
      continue
    for i,row in enumerate(rows):
      if i==0 and n_out>0: continue #1 header only
      fout.write('%s\n'%(row))
      n_out+=1
  print('sids in: %d'%len(ids), file=sys.stderr)
  print('assay summaries out: %d'%n_out, file=sys.stderr)
  print('errors: %d'%n_err, file=sys.stderr)

#############################################################################
def Cids2Properties(base_url,ids,fout,verbose):
  ## Use method POST; put CIDs in data.
  ids_txt='cid='+(','.join(map(lambda x:str(x),ids)))
  #print('DEBUG: ids_txt = %s'%ids_txt, file=sys.stderr)
  req=urllib.request.Request(url=base_url+'/compound/cid/property/IsomericSMILES,MolecularFormula,MolecularWeight,XLogP,TPSA/CSV',
	headers={'Accept':OFMTS['CSV'],'Content-type':'application/x-www-form-urlencoded'},
	data=ids_txt)
  f=urllib.request.urlopen(req)
  while True:
    line=f.readline()
    if not line: break
    fout.write(line)

#############################################################################
def Cids2Inchi(base_url,ids,fout,verbose):
  ## Use method POST; put CIDs in data.
  ids_txt='cid='+(','.join(map(lambda x:str(x),ids)))
  #print('DEBUG: ids_txt = %s'%ids_txt, file=sys.stderr)
  req=urllib.request.Request(url=base_url+'/compound/cid/property/InChI,InChIKey/CSV',
	headers={'Accept':OFMTS['CSV'],'Content-type':'application/x-www-form-urlencoded'},
	data=ids_txt)
  f=urllib.request.urlopen(req)
  while True:
    line=f.readline()
    if not line: break
    fout.write(line)

#############################################################################
### Request in chunks.  Works for 50, and not for 200 (seems to be a limit).
#############################################################################
def Cids2Sdf(base_url,ids,fout,verbose):
  nchunk=50; nskip_this=0;
  while True:
    if nskip_this>=len(ids): break
    idstr=(','.join(map(lambda x:str(x),ids[nskip_this:nskip_this+nchunk])))
    d={'cid':idstr}
    txt=rest_utils.PostURL(base_url+'/compound/cid/SDF',data=d,verbose=verbose)
    fout.write(txt)
    nskip_this+=nchunk
  return

#############################################################################
### Request in chunks.  Works for 50, and not for 200 (seems to be a limit).
#############################################################################
def Sids2Sdf(base_url,sids,fout,skip,nmax,verbose):
  n_sid_in=0; n_sdf_out=0;
  if verbose:
    if skip: print('skip: [1-%d]'%skip, file=sys.stderr)
  nchunk=50; nskip_this=skip;
  while True:
    if nskip_this>=len(sids): break
    nchunk=min(nchunk,nmax-(nskip_this-skip))
    n_sid_in+=nchunk
    idstr=(','.join(map(lambda x:str(x),sids[nskip_this:nskip_this+nchunk])))
    txt=rest_utils.PostURL(base_url+'/substance/sid/SDF',data={'sid':idstr},verbose=verbose)
    if txt:
      fout.write(txt)
      eof = re.compile(r'^\$\$\$\$',re.M)
      n_sdf_out_this = len(eof.findall(txt))
      n_sdf_out+=n_sdf_out_this

    nskip_this+=nchunk
    if nmax and (nskip_this-skip)>=nmax:
      print('NMAX limit reached: %d'%nmax, file=sys.stderr)
      break

  #print('sids in: %d ; sdfs out: %d'%(n_sid_in,n_sdf_out), file=sys.stderr)

  return n_sid_in,n_sdf_out

#############################################################################
### Request returns CSV format CID,"SMILES" which must be fixed.
#############################################################################
def Cids2Smiles(base_url,ids,isomeric,fout,verbose):
  t0 = time.time()
  nchunk=50; nskip_this=0;
  n_in=0; n_out=0; n_err=0;
  while True:
    if nskip_this>=len(ids): break
    ids_this = ids[nskip_this:nskip_this+nchunk]
    n_in+=len(ids_this)
    idstr=(','.join(map(lambda x:str(x),ids_this)))
    d={'cid':idstr}
    prop = 'IsomericSMILES' if isomeric else 'CanonicalSMILES'
    txt=rest_utils.PostURL(base_url+'/compound/cid/property/%s/CSV'%prop,data=d,verbose=verbose)
    if not txt:
      n_err+=1
      break
    lines=txt.splitlines()
    for line in lines:
      cid,smi = re.split(',',line)
      if cid.upper()=='CID': continue #header
      try:
        cid=int(cid)
      except:
        continue
      smi=smi.replace('"','')
      fout.write('%s %d\n'%(smi,cid))
      n_out+=1
    nskip_this+=nchunk
    if verbose>0 and (n_in%1000)==0:
      print('processed: %6d / %6d (%.1f%%); elapsed time: %s'%(n_in,len(ids), 100.0*n_in/len(ids),time_utils.NiceTime(time.time()-t0)), file=sys.stderr)
  print('cids in: %d'%n_in, file=sys.stderr)
  print('smiles out: %d'%n_out, file=sys.stderr)
  print('errors: %d'%n_err, file=sys.stderr)
  return

#############################################################################
def Inchi2Cids(base_url,inchi,verbose):
  '''	Must be POST with "Content-Type: application/x-www-form-urlencoded"
	or "Content-Type: multipart/form-data" with the POST body formatted accordingly.
	See: http://pubchem.ncbi.nlm.nih.gov/pug_rest/PUG_REST.html and
	http://pubchem.ncbi.nlm.nih.gov/pug_rest/PUG_REST_Tutorial.html
  '''
  ofmt='TXT'
  #ofmt='XML'
  cid=None
  url="http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchi/cids/%s"%ofmt ### URL ok?
  #body_data=('\n'.join(map(lambda x:urllib.parse.quote(x),inchis)))
  body_data=('inchi='+urllib.parse.quote(inchi))
  req=urllib.request.Request(url=url,
	headers={'Content-Type':'application/x-www-form-urlencoded','Accept':OFMTS[ofmt]},
	data=body_data)
  if verbose>1:
    print('url="%s"; inchi="%s"'%(url,inchi), file=sys.stderr)
  #print('DEBUG: req.get_type() = %s'%req.get_type(), file=sys.stderr)
  #print('DEBUG: req.get_method() = %s'%req.get_method(), file=sys.stderr)
  #print('DEBUG: req.get_host() = %s'%req.get_host(), file=sys.stderr)
  #print('DEBUG: req.get_full_url() = %s'%req.get_full_url(), file=sys.stderr)
  #print('DEBUG: req.header_items() = %s'%req.header_items(), file=sys.stderr)
  #print('DEBUG: req.get_data() = %s'%req.get_data(), file=sys.stderr)
  #
  f=urllib.request.urlopen(req)
  
  cids=[]
  while True:
    line=f.readline()
    if not line: break
    try:
      cid=int(line)
      cids.append(cid)
    except:
      pass
  return cids

#############################################################################
def Aid2DescriptionXML(base_url,id_query,verbose=0):
  x=rest_utils.GetURL(base_url+'/assay/aid/%d/description/XML'%id_query,verbose=verbose)
  return x

#############################################################################
def GetAssayDescriptions(base_url,ids,fout,skip,nmax,verbose=0):
  import xpath
  fout.write('ID,Source,Name,Target,Date\n')
  adesc_xpath='/PC-AssayContainer/PC-AssaySubmit/PC-AssaySubmit_assay/PC-AssaySubmit_assay_descr/PC-AssayDescription'
  tag_name='PC-AssayDescription_name'
  tag_source='PC-DBTracking_name'
  tag_year='Date-std_year'
  tag_month='Date-std_month'
  tag_day='Date-std_day'
  tag_tgtname='PC-AssayTargetInfo_name'
  n_in=0; n_out=0;
  for aid in ids:
    n_in+=1
    if skip and n_in<skip: continue
    if nmax and n_out==nmax: break
    xmlstr=rest_utils.GetURL(base_url+'/assay/aid/%d/description/XML'%aid,verbose=verbose)
    dom=xml.dom.minidom.parseString(xmlstr)
    desc_nodes = xpath.find(adesc_xpath,dom)
    for desc_node in desc_nodes:
      name=xpath.findvalue('//%s'%tag_name,desc_node)
      source=xpath.findvalue('//%s'%tag_source,desc_node)
      year=xpath.findvalue('//%s'%tag_year,desc_node)
      month=xpath.findvalue('//%s'%tag_month,desc_node)
      day=xpath.findvalue('//%s'%tag_day,desc_node)
      ymd = (year+month+day) if (year and month and day) else ''
      tgtname=xpath.findvalue('//%s'%tag_tgtname,desc_node)
      fout.write('%d,"%s","%s","%s",%s\n'%(aid,source,name,(tgtname if tgtname else ''),ymd))
      n_out+=1

#############################################################################
def OutcomeCode(txt):
  return OUTCOME_CODES[txt.lower()] if txt.lower() in OUTCOME_CODES else OUTCOME_CODES['unspecified']

#############################################################################
def GetAssayResults_Screening2(base_url,aids,sids,fout,skip,nmax,verbose=0):
  '''One CSV line for each activity.  skip and nmax applied to AIDs.
In this version of the function, use the "concise" mode to download full data
for each AID, then iterate through SIDs and use local hash.
'''
  if verbose:
    if skip: print('skip: [1-%d]'%skip, file=sys.stderr)
    if nmax: print('NMAX: %d'%nmax, file=sys.stderr)
  n_aid_in=0; n_aid_done=0; n_out=0;
  nchunk_sid=100;
  #fout.write('aid,sid,outcome,version,rank,year\n')
  tags = None
  for aid in aids:
    n_aid_in+=1
    n_out_this=0;
    if skip and n_aid_in<skip: continue
    if nmax and n_aid_done>=nmax: break
    n_aid_done+=1
    if verbose>1:
      print('Request: (%d) [AID=%d] SID count: %d'%(n_aid_done,aid,len(sids)), file=sys.stderr)
    try:
      url = base_url+'/assay/aid/%d/concise/JSON'%(aid)
      print('DEBUG: %s'%(url), file=sys.stderr)
      rval = rest_utils.GetURL(url,parse_json=True,verbose=verbose)
    except Exception as e:
      print('Error: %s'%(e), file=sys.stderr)
      break

    if not type(rval)==types.DictType:
      #print('Error: %s'%(str(rval)), file=sys.stderr)
      f = open("z.z", "w")
      f.write(str(rval))
      f.close()
      print('DEBUG: rval not DictType.  See z.z', file=sys.stderr)
      break
    adata = {} # data this assay
    tags_this = rval["Table"]["Columns"]["Column"]
    print('DEBUG: tags_this = %s'%(str(tags_this)), file=sys.stderr)
    j_sid = None;
    j_res = None;
    if not tags:
      tags = tags_this
      for j,tag in enumerate(tags):
        if tag == 'SID': j_sid = j
        if tag == 'Bioactivity Outcome': j_res = j
      fout.write(','.join(tags)+'\n')

    rows = rval["Table"]["Row"]

    for row in rows:
      cells = row["Cell"]
      if len(cells) != len(tags):
        print('Error: n_cells != n_tags (%d != %d)'%(len(cells), len(tags)), file=sys.stderr)
        continue

      #fout.write(','.join(cells)+'\n')
      sid = cells[j_sid]
      res = cells[j_res]
      adata[sid] = res

      #break #DEBUG

#############################################################################
def GetAssayResults_Screening(base_url,aids,sids,fout,skip,nmax,verbose=0):
  '''One CSV line for each activity.  skip and nmax applied to AIDs.
Must chunk the SIDs, since requests limited to 10k SIDs.
'''
  if verbose:
    if skip: print('skip: [1-%d]'%skip, file=sys.stderr)
    if nmax: print('NMAX: %d'%nmax, file=sys.stderr)
  n_aid_in=0; n_aid_done=0; n_out=0;
  nchunk_sid=100;
  fout.write('aid,sid,outcome,version,rank,year\n')
  for aid in aids:
    n_aid_in+=1
    n_out_this=0;
    if skip and n_aid_in<skip: continue
    if nmax and n_aid_done>=nmax: break
    n_aid_done+=1
    if verbose>1:
      print('Request: (%d) [AID=%d] SID count: %d'%(n_aid_done,aid,len(sids)), file=sys.stderr)
    nskip_sid=0;
    while True:
      if nskip_sid>=len(sids): break
      if verbose>1:
        print('(%d) [AID=%s] ; SIDs [%d-%d of %d] ; measures: %d'%(n_aid_done,aid,nskip_sid+1,min(nskip_sid+nchunk_sid,len(sids)),len(sids),n_out_this), file=sys.stderr)
      sidstr=(','.join(map(lambda x:str(x),sids[nskip_sid:nskip_sid+nchunk_sid])))
      try:
        rval = rest_utils.GetURL(base_url+'/assay/aid/%d/JSON?sid=%s'%(aid,sidstr),parse_json=True,verbose=verbose)
      except Exception as e:
        print('Error: %s'%(e), file=sys.stderr)
        break
      if not type(rval)==types.DictType:
        print('Error: %s'%(str(rval)), file=sys.stderr)
        break
      pcac = rval['PC_AssayContainer'] if 'PC_AssayContainer' in rval else None
      if len(pcac)<1:
        print('Error: [%s] empty PC_AssayContainer.'%aid, file=sys.stderr)
        break
      if len(pcac)>1:
        print('NOTE: [%s] multiple assays in PC_AssayContainer.'%aid, file=sys.stderr)
      for assay in pcac:
        if not assay: continue
        if verbose>2:
          print(json.dumps(assay,indent=2), file=sys.stderr)
        ameta = assay['assay'] if 'assay' in assay else None
        adata = assay['data'] if 'data' in assay else None
        if not ameta: print('Error: [%s] no metadata.'%aid, file=sys.stderr)
        if not adata: print('Error: [%s] no data.'%aid, file=sys.stderr)
        for datum in adata:
          sid = datum['sid'] if 'sid' in datum else ''
          outcome = datum['outcome'] if 'outcome' in datum else ''
          version = datum['version'] if 'version' in datum else ''
          rank = datum['rank'] if 'rank' in datum else ''
          date = datum['date'] if 'date' in datum else {}
          year = date['std']['year'] if 'std' in date and 'year' in date['std'] else ''
          fout.write('%d,%s,%d,%s,%s,%s\n'%(aid,sid,OutcomeCode(outcome),version,rank,year))
          fout.flush()
          n_out_this+=1
      nskip_sid+=nchunk_sid
    if verbose>1:
      print('Result: [AID=%d] total measures: %d'%(aid,n_out_this), file=sys.stderr)

  return n_aid_in,n_out

#############################################################################
def AssayXML2NameAndSource(xmlstr):
  '''Required: xpath - XPath Queries For DOM Trees, http://py-dom-xpath.googlecode.com/'''
  import xpath
  dom=xml.dom.minidom.parseString(xmlstr)
  tag_name='PC-AssayDescription_name'
  name=xpath.findvalue('//%s'%tag_name,dom)  ##1st
  tag_source='PC-DBTracking_name'
  source=xpath.findvalue('//%s'%tag_source,dom)  ##1st
  return name,source

#############################################################################
def DescribeAssay(base_url,id_query,verbose=0):
  rval=rest_utils.GetURL(base_url+'/assay/aid/%d/description/JSON'%id_query,parse_json=True,verbose=verbose)
  #print(json.dumps(rval,indent=2), file=sys.stderr)
  assays = rval['PC_AssayContainer']
  print('aid,name,assay_group,project_category,activity_outcome_method')
  for assay in assays:
    aid = assay['assay']['descr']['aid']['id']
    name = assay['assay']['descr']['name']
    assay_group = assay['assay']['descr']['assay_group'][0]
    project_category = assay['assay']['descr']['project_category']
    activity_outcome_method = assay['assay']['descr']['activity_outcome_method']
    vals = [aid,name,assay_group,project_category,activity_outcome_method]
    print(','.join(map(lambda s: '"%s"'%s, vals)))
  return

#############################################################################
def Name2Sids(base_url,name,verbose):
  d=rest_utils.GetURL(base_url+'/substance/name/%s/sids/JSON'%urllib.parse.quote(name),parse_json=True,verbose=verbose)
  #return d[u'IdentifierList'][u'SID']
  return d['IdentifierList']['SID']

#############################################################################
def Sid2Synonyms(base_url,sid,verbose):
  d=rest_utils.GetURL(base_url+'/substance/sid/%d/synonyms/JSON'%(sid),parse_json=True,verbose=verbose)
  if not d: return []
  #if not type(d) is types.DictType: return []
  try:
    infos = d['InformationList']['Information']
  except Exception as e:
    print('Error (Exception): %s'%e, file=sys.stderr)
    print('DEBUG: d = %s'%str(d), file=sys.stderr)
    return []
  if not infos: return []
  synonyms=[]
  for info in infos:
    synonyms.extend(info['Synonym'])
  return synonyms

#############################################################################
def Cid2Synonyms(base_url,cid,verbose):
  sids = Cid2Sids(base_url,cid,verbose)
  if verbose:
    print('cid=%d: sid count: %d'%(cid,len(sids)), file=sys.stderr)
  synonyms = set([])
  for sid in sids:
    synonyms_this = Sid2Synonyms(base_url,sid,verbose)
    synonyms |= set(synonyms_this)
  return list(synonyms)

#############################################################################
def Cids2Synonyms(base_url,cids,fout,skip,nmax,verbose):
  fout.write('"cid","sids","synonyms"\n')
  sids = set([])
  i_cid=0;
  for cid in cids:
    i_cid+=1
    if skip and i_cid<=skip: continue
    sids_this = Cid2Sids(base_url,cid,verbose)
    sids |= set(sids_this)
    synonyms = set([])
    for sid in sids_this:
      synonyms_this = Sid2Synonyms(base_url,sid,verbose)
      synonyms |= set(synonyms_this)
    synonyms_nice = SortCompoundNamesByNiceness(list(synonyms))[:10]
    fout.write('%d,"%s","%s"\n'%(
	cid,
	';'.join(map(lambda x:str(x),sids_this)),
	';'.join(synonyms_nice)))
    if verbose:
      if synonyms_nice: s1=synonyms_nice[0]
      else: s1=None
      print('%d. cid=%d: sids: %d ; synonyms: %d (%s)'%(i_cid,cid,len(sids_this),len(synonyms),s1), file=sys.stderr)
    fout.flush()
    if nmax and i_cid>=(skip+nmax): break
  if verbose:
    print('total sids: %d'%(len(sids)), file=sys.stderr)

#############################################################################
def Name2Cids(base_url,name,verbose):
  sids=Name2Sids(base_url,name,verbose)
  cids={}
  for cid in Sids2Cids(base_url,sids,verbose):
    cids[cid]=True
  cids=cids.keys()
  cids.sort() 
  return cids

#############################################################################
def NameNicenessScore(name):
  score=0;
  pat_proper = re.compile(r'^[A-Z][a-z]+$')
  pat_text = re.compile(r'^[A-Za-z ]+$')
  if pat_proper.match(name): score+=100
  elif pat_text.match(name): score+=50
  elif re.match(r'^[A-z][A-z][A-z][A-z][A-z][A-z][A-z].*$',name): score+=10
  if re.search(r'[\[\]\{\}]',name): score-=50
  if re.search(r'[_/\(\)]',name): score-=10
  if re.search(r'\d',name): score-=10
  score -= math.fabs(7-len(name))    #7 is optimal!
  return score

#############################################################################
### Heuristic for human comprehensibility.
#############################################################################
def SortCompoundNamesByNiceness(names):
  names_scored = {n:NameNicenessScore(n) for n in names}
  names_ranked = [[score,name] for name,score in names_scored.items()]
  names_ranked.sort()
  names_ranked.reverse()
  return [name for score,name in names_ranked]

#############################################################################
def GetCpdAssayStats(base_url,cid,smiles,aidset,fout_mol,fout_act,aidhash,verbose):
  aids_tested=set(); aids_active=set();
  sids_tested=set(); sids_active=set();
  n_sam=0; n_sam_active=0; mol_active=False; mol_found=False;

  try:
    fcsv=rest_utils.GetURL(base_url+'/compound/cid/%d/assaysummary/CSV'%cid,verbose=verbose)
  except urllib.request.HTTPError as e:
    print('ERROR: [%d] REST request failed; response code = %d'%(cid,e.code), file=sys.stderr)
    #if not e.code in http_errs: http_errs[e.code]=1
    #else: http_errs[e.code]+=1
    fout_mol.write("%s %d\n"%(smiles,cid))
    return mol_found,mol_active,n_sam,n_sam_active
  except Exception as e:
    print('ERROR: [%d] REST request failed; %s'%(cid,e), file=sys.stderr)
    fout_mol.write("%s %d\n"%(smiles,cid))
    return mol_found,mol_active,n_sam,n_sam_active
  mol_found=True

  try:
    csvReader=csv.DictReader(fcsv.splitlines(),fieldnames=None,restkey=None,restval=None,dialect='excel',delimiter=',',quotechar='"')
    csvrow=csvReader.next()    ## must do this to get fieldnames
  except Exception as e:
    print('ERROR: [CID=%d] CSV problem:%s'%(cid,e), file=sys.stderr)
    fout_mol.write("%s %d\n"%(smiles,cid))
    return mol_found,mol_active,n_sam,n_sam_active

  for field in ('AID','CID','SID','Bioactivity Outcome','Bioassay Type'):
    if field not in csvReader.fieldnames:
      print('ERROR: [CID=%d] bad CSV header, no "%s" field.'%(cid,field), file=sys.stderr)
      print('DEBUG: fieldnames: %s'%(','.join(map((lambda x:'"%s"'%x),csvReader.fieldnames))), file=sys.stderr)
      fout_mol.write("%s %d\n"%(smiles,cid))
      return mol_found,mol_active,n_sam,n_sam_active

  n_in=0
  while True:
    try:
      csvrow=csvReader.next()
    except:
      break  ## EOF
    n_in+=1

    try:
      aid=int(csvrow['AID'])
      sid=int(csvrow['SID'])
      csvrow_cid=int(csvrow['CID'])
    except:
      print('ERROR: [CID=%d] bad CSV line; problem parsing: "%s"'%(cid,str(csvrow)), file=sys.stderr)
      continue
    if cid!=csvrow_cid:
      print('ERROR: Aaack! [CID=%d] CID mismatch: != %d'%(cid,csvrow_cid), file=sys.stderr)
      return mol_found,mol_active,n_sam,n_sam_active

    if aidset:
      if aid not in aidset:
        continue
      #print('DEBUG: AID [%d] ok (pre-selected).'%(aid), file=sys.stderr)

    ## Assay filtering done; now update statistics (sTested, sActive).
    n_sam+=1
    aidhash[aid]=True
    act_outcome=csvrow['Bioactivity Outcome'].lower()
    if act_outcome in OUTCOME_CODES:
      fout_act.write("%d,%d,%d,%d\n"%(cid,sid,aid,OUTCOME_CODES[act_outcome]))
    else:
      if verbose>2:
        print('[%d] unrecognized outcome (CID=%d,AID=%d): "%s"'%(n_in,cid,aid,act_outcome), file=sys.stderr)

    aids_tested.add(aid)
    sids_tested.add(sid)
    if act_outcome=='active':
      n_sam_active+=1
      mol_active=True
      aids_active.add(aid)
      sids_active.add(sid)

  if verbose>2:
    print('[CID=%d] CSV data lines: %d'%(cid,n_in), file=sys.stderr)

  fout_mol.write("%s %d %d %d %d %d %d %d\n"%(
	smiles,
	cid,
	len(sids_tested),
	len(sids_active),
	len(aids_tested),
	len(aids_active),
	n_sam,
	n_sam_active))
  if verbose>1:
    print("cid=%d,sTested=%d,sActive=%d,aTested=%d,aActive=%d,wTested=%d,wActive=%d"%(
	cid,
	len(sids_tested),
	len(sids_active),
	len(aids_tested),
	len(aids_active),
	n_sam,
	n_sam_active), file=sys.stderr)

  return mol_found,mol_active,n_sam,n_sam_active

#############################################################################
def GetCpdAssayData(base_url,cid_query,aidset,fout,verbose):
  try:
    fcsv=rest_utils.GetURL(base_url+'/compound/cid/%d/assaysummary/CSV'%cid_query,verbose=verbose)
  except Exception as e:
    print('ERROR: [%d] REST request failed; %s'%(cid_query,e), file=sys.stderr)
    return False

  if not fcsv:
    return False

  try:
    csvReader=csv.DictReader(fcsv.splitlines(),fieldnames=None,restkey=None,restval=None,dialect='excel',delimiter=',',quotechar='"')
    csvrow=csvReader.next()    ## must do this to get fieldnames
  except Exception as e:
    print('ERROR: [CID=%d] CSV problem: %s'%(cid_query,e), file=sys.stderr)
    return True

  for field in ('CID','SID','AID','Bioactivity Outcome','Activity Value [uM]'):
    if field not in csvReader.fieldnames:
      print('ERROR: [CID=%d] bad CSV header, no "%s" field.'%(cid_query,field), file=sys.stderr)
      print('DEBUG: fieldnames: %s'%(','.join(map((lambda x:'"%s"'%x),csvReader.fieldnames))), file=sys.stderr)
      return True

  n_in=0; n_act=0;
  while True:
    try:
      csvrow=csvReader.next()
    except:
      break  ## EOF
    n_in+=1
    try:
      aid=int(csvrow['AID'])
      sid=int(csvrow['SID'])
      cid=int(csvrow['CID'])
      outcome=csvrow['Bioactivity Outcome']
    except:
      print('ERROR: [CID=%d] bad CSV line; problem parsing.'%cid, file=sys.stderr)
      #print('DEBUG: csvrow = %s'%str(csvrow), file=sys.stderr)
      continue
    if cid_query!=cid:
      print('ERROR: Aaack! [CID=%d] CID mismatch: != %d'%(cid,int(csvrow['CID'])), file=sys.stderr)
      return True
    if aid not in aidset:
      continue
      #print('DEBUG: AID [%d] ok (pre-selected).'%(aid), file=sys.stderr)

    if not csvrow['Activity Value [uM]']:
      continue

    try:
      actval=float(csvrow['Activity Value [uM]'])
    except:
      print('ERROR: [CID=%d] bad CSV line; problem parsing activity: "%s"'%(cid,csvrow['Activity Value [uM]']), file=sys.stderr)
      continue

    n_act+=1
    outcome_code = OUTCOME_CODES[outcome.lower()] if outcome.lower() in OUTCOME_CODES else 0

    fout.write('%d,%d,%d,%d,%.3f\n'%(cid,sid,aid,outcome_code,actval))

  print('[CID=%d] records: %2d ; activities: %2d'%(cid_query,n_in,n_act), file=sys.stderr)
  return True

#############################################################################
if __name__=='__main__':

  if len(sys.argv)<2:
    print('Syntax: %s NAMEFILE'%sys.argv[0])
    sys.exit(1)

  fin = open(sys.argv[1])
  while True:
    line = fin.readline()
    if not line: break
    name=line.rstrip()
    print('%s\t%d'%(name,NameNicenessScore(name)))