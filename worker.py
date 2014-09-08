import db
import bitsource
import requests

def parse(message):
  a=[]
  for x in message:
    j=ord(x)
    if j<48 or (j>57 and j<65) or (j>90 and j<96) or j>122:
      a.append(63)
    else:
      a.append(ord(x))

  c=""
  for b in a:
    c=c+chr(b)
  return c


def add_message_to_db(message, block, txhash):
  dbstring = "INSERT INTO MESSAGES (message, block, txhash) VALUES ('"+str(message)+"','"+str(block)+"','"+str(txhash)+"');"
  print dbstring
  response=db.dbexecute(dbstring, False)
  return response

def block_opreturns_to_db(blockn):
  data=bitsource.opreturns_in_block_blockchain(blockn)

  for x in data:
    txhash=str(x[0])
    #message=parse(str(x[1]))
    message=str(x[1])
    if len(message)>40:
      message=message[0:40]
    print message

    k=add_message_to_db(message, str(blockn), txhash)
    print k
  db.dbexecute("UPDATE META SET lastblockdone='" + str(blockn)+"';",False)

def moreblocks(number):
  lastblock=db.dbexecute("SELECT * FROM META;",True)
  lastblock=lastblock[0][0]
  currentblock=int(requests.get("https://blockchain.info/q/getblockcount").content)

  endtarget=lastblock+number
  if endtarget>currentblock:
    endtarget=currentblock

  for i in range(lastblock+1, endtarget+1):
    block_opreturns_to_db(i)
    print "processed block "+str(i)+" for opreturns"


import time

def work():
  start=time.time()
  interval=30
  while True:
    if time.time()>=interval+start:
      start=time.time()
      moreblocks(30)

work()
