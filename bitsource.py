import requests
import json
import time
import leb128
import node
import cointools


def getblockmeta(n):
  #get hash of block at height n
  blockhash=node.connect('getblockhash',[n])

  blockdata=node.connect('getblock',[blockhash])
  return blockdata


def getrawtx(txhash):
  txdata=node.connect('getrawtransaction',[txhash])
  return txdata


def tx_lookup(txhash):
   #print txhash
   c=node.connect('getrawtransaction',[txhash,1])
   return c


def tx_inputs(txhash):
  txdata=tx_lookup(txhash)

  global prevtxidsq
  automatic=False
  txins=txdata['vin']
  prevtxids=[]
  for x in txins:
    if 'txid' in x: #is normal transaction, not automatic block reward
      prevtxids.append([x['txid'],x['vout']])
    else:
      height=node.connect('getblock',[txdata['blockhash']])['height']
      prevtxids.append(height)
      automatic=True

  answer={}

  if automatic==False:
    #who was the destination of that txid,outputn pair?
    answer['inputs']=[]
    for a in prevtxids:
      data=tx_lookup(a[0])
      address=data['vout'][a[1]]['scriptPubKey']['addresses'][0]  #ONLY ONE ADDRESS PER OUTPUT!!!
      amount=data['vout'][a[1]]['value']
      f={}
      f['address']=address
      f['amount']=amount
      f['txid']=a[0]
      answer['inputs'].append(f)
  else:
    answer['block']=prevtxids[0]

  return answer


def gettx(txhash):
  a=tx_lookup(txhash)
  b=tx_inputs(txhash)
  c= dict(a.items() + b.items())
  return c


def txs_in_block(n):
  starttime=time.time()
  a=getblockmeta(n)
  t=[]
  j=0
  g=str(len(a['tx']))
  for x in a['tx']:
    j=j+1
    print str(j)+" / "+g
    t.append(gettx(x))
  duration=time.time()-starttime
  print "This took: "+str(duration)+" seconds"
  return t


def script_to_coloraddress(script):
  ripehash=leb128.ripehash(script)
  answer=cointools.base58CheckEncode(0x05, ripehash.decode('hex'))
  return answer


def color_address(publicaddress):
  a=requests.get('https://blockexplorer.com/q/addresstohash/')
  hashed=a.content  #REPLACE THIS METHOD


def read_tx(txhash):
  r=tx_lookup(txhash)
  m=-1
  if 'vout' in r:
    v=0
    for x in r['vout']:
      if 'value' in x:
        v=v+x['value']
      if x['scriptPubKey']['hex'][0:2]=='6a': #OP RETURN, only 1 per tx
        d=x['scriptPubKey']['hex']
        m=d[2:len(d)]
        m=m.decode('hex')
        m=m[1:len(m)]
        #return m
    #if m=='':
      #return -1
  return m, v


def op_return_in_block(n):
  blockmeta=getblockmeta(n)
  txhashes=blockmeta['tx']
  results=[]
  messages=[]
  for tx in txhashes:
    #print tx
    n=read_tx(tx)
    m=n[0]
    if not m==-1:
      messages.append([tx,m,n[1]])
  return messages


def opreturns_in_block_blockchain(n):
  a=requests.get("http://blockchain.info/block-height/"+str(n)+"?format=json").content
  a=json.loads(a)
  for x in a['blocks']:
    if x['main_chain']:
      a=x
  txs=a['tx']
  answers=[]
  for tx in txs:
    for out in tx['out']:
      script=out['script']
      if script[0:2]=="6a":
        script=script[4:len(script)]
        script=script.decode("hex")
        answers.append([tx['hash'],script])
  return answers


def parse_colored_tx(metadata, txhash_with_index):
  global d,e,g, count,f, hexmetadata
  hexmetadata=metadata.encode('hex')
  opcode=metadata[0:2]
  results={}
  if opcode=='OA': #then OA
      results['type']='OA'
      results['version']=metadata[2:4].encode('hex')
      results['asset_count']=int(metadata[4:5].encode('hex'))

      count=0
      d=[]
      for x in metadata[5:len(metadata)]:
        r=leb128.hexpiecetobinary(x.encode('hex'))
        d.append(r)
      e=[]
      r=[]
      for x in d:
        r.append(x)
        if x[0]=='0':
          e.append(r)
          r=[]
      f=[]

      n=0
      for x in e:
        if n<int(results['asset_count'])+1:
          f.append(leb128.decode(x))
          count=count+len(x)
        n=n+1

      results['asset_quantities']=f[0:len(f)-1]
      results['metadata_length']=f[len(f)-1]
      results['metadata']=metadata[5+count:len(metadata)]

      r=txhash_with_index.index(":")
      markerposition=int(txhash_with_index[r+1:len(txhash_with_index)])
      txhash=txhash_with_index[0:r]
      txdata=tx_lookup(txhash)
      txoutputs=txdata['vout']
      results['issued']=[]
      for i in range(0,markerposition):
        h={}
        h['quantity']=results['asset_quantities'][i]

        #assumes first input is correct input....??!
        script=tx_lookup(txdata['vin'][0]['txid'])['vout'][txdata['vin'][0]['vout']]['scriptPubKey']['hex']
        print script
        h['txhash_index']=txhash+":"+str(i)
        h['color_address']=script_to_coloraddress(script)
        h['destination_address']=txoutputs[i]['scriptPubKey']['addresses'][0] #one dest per output
        h['btc']=int(txoutputs[i]['value']*100000000)
        h['previous_inputs']="source:"+str(tx_lookup(txdata['vin'][0]['txid'])['vout'][txdata['vin'][0]['vout']]['scriptPubKey']['addresses'][0])
        results['issued'].append(h)

      results['transferred']=[]
      for i in range(markerposition+1, len(txoutputs)):
        if i<=len(results['asset_quantities']):
          h={}
          h['out_n']=i
          h['txhash_index']=txhash+":"+str(i)
          h['quantity']=results['asset_quantities'][i-1]
          h['color_address']="" #FIGURE THIS PART OUT

          h['previous_inputs']=[]
          for x in txdata['vin']:
            h['previous_inputs'].append(str(x['txid'])+":"+str(x['vout']))
        #    txdata['vin'][i-1]['txid']+":"+str(txdata['vin'][i-1]['vout'])   #ASSUMES ONE TO ONE CORRESPONDENCE, NOT ALWAYS TRUE

          print txoutputs[i-1]
          h['destination_address']=txoutputs[i]['scriptPubKey']['addresses'][0]
          h['btc']=int(txoutputs[i]['value']*100000000)
          results['transferred'].append(h)



  return results


def write_metadata(asset_quantities, otherdata):
  #PLAINTEXT SCRIPT TO BE ENCODED INTO OP RETURN using Transaction.make_info_script
  global encoded
  #work in hex
  result='4f410100' #OA + version 0100
  assetcount=str(len(asset_quantities))
  if len(assetcount)==1:
    assetcount='0'+assetcount
  result=result+assetcount

  for asset in asset_quantities:

    encoded=leb128.encode(asset)
    j=''
    for x in encoded:
      r=str(hex(int(x,2)))
      if len(r)==3:
        r='0'+r[2:3]
      else:
        r=r[2:len(r)]
      j=j+r

    result=result+j

  length=hex(len(otherdata))
  if len(length)==3:
    length=length[2:len(length)]
    length='0'+length
  else:
    length=length[2:len(length)]
  result=result+length
  result=result+otherdata.encode('hex')

  return result
  #result=result+"\x"+assetcount



def oa_tx(txid, inputcolors):
  txdata=tx_lookup(txid)
  message=read_tx(txid)
  message=message[0]
  isOA=False
  markerposition=-1
  result={}

  #find marker position and ascertain whether OA
  for x in txdata['vout']:
    if x['scriptPubKey']['hex'][0:2]=='6a' and isOA==False and x['scriptPubKey']['hex'][4:8]=='4f41':
      isOA=True
      markerposition= x['n']

  #INPUT COLORS IS ARRAY OF DICTIONARIES [ {'color_address':'', 'amount':''}]
  #Tabulate sums of inputs of different colors
  inputsums={}
  for x in inputcolors:
    inputsums[x['color_address']]= inputsums[x['color_address']]+ x['amount']

  #If it is OA
  if isOA:
    #get meta data
    result['meta']=parse_colored_tx(message)
    result['txid']= txdata['txid']

    #Describe Issuing Outputs
    result['issued']=[]
    for i in range(0,markerposition):
      k={}
      amt= result['meta']['asset_quantities'][i]
      k['amount']=amt
      k['color_address']=''   #FIGURE THIS PART OUT
      k['destination_address']= txdata['vout'][i]['scriptPubKey']['addresses'][0] #ONLY EVER ONE ADDRESS PER OUTPUT
      k['output_n']=i
      result['issued'].append(k)

    #Describe Transfer Outputs
    result['transferred']=[]
    for i in range(markerposition,len(txdata['vout'])):
      k={}
      supposedamt= result['meta']['assetquantities'][i]  #MIGHT BE WRONG i
      k['color_address']=''

      if supposedamt<= inputsums[k['color_address']]: #THERE IS ENOUGH TO TRANSFER
        amt=supposedamt

      k['amount']=amt

      k['destination_address']= txdata['vout'][i]['scriptPubKey']['addresses'][0]
      k['output_n']=i
      result['transferred'].append(k)

  return result


def oa_in_block(n):
  messages=op_return_in_block(n)
  global markerposition
  results=[]
  for x in messages:
    metadata=x[1]
    r={}

    isOA=False

    txdata=tx_lookup(x[0])  #REDUNDANT CALL
    #POSITION OF MARKER OUTPUT IN ALL OUTPUTS
    markerposition=-1
    for x in txdata['vout']:
      #MIGHT BE ISSUE HERE WITH OP_PUSHDATA
      if x['scriptPubKey']['hex'][0:2]=='6a' and isOA==False and x['scriptPubKey']['hex'][4:8]=='4f41':
         #IS OPRETURN and is OA
         isOA=True
         markerposition= x['n']

    if isOA:
      r['meta']=parse_colored_tx(metadata)
      r['txid']= txdata['txid']

      r['issued']=[]
      for i in range(0,markerposition):
        k={}
        amt= r['meta']['asset_quantities'][i]
        k['amount']=amt
        k['color_address']=''   #FIGURE THIS PART OUT
        k['destination_address']= txdata['vout'][i]['scriptPubKey']['addresses'][0] #ONLY EVER ONE ADDRESS PER OUTPUT
        r['issued'].append(k)

      r['transferred']=[]




      results.append(r)

  return results
