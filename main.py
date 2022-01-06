import discord
from etherscan import Etherscan
import os
import re
import time
from dotenv import load_dotenv
load_dotenv()
from web3.auto.infura import w3
from web3.ens import ENS
ns = ENS.fromWeb3(w3)

from discord.ext import tasks

last_block = 0
eth = Etherscan(os.environ['ETHERSCAN_API_KEY'])
watch_list = ['0x2d407ddb06311396fe14d4b49da5f0471447d45c']
client = discord.Client()


async def ensName(addr):
    ens = ns.name(addr)
    if ens is None:
        return addr
    else:
        return ens


async def getLatestTxn(last_block):
    new_updates = []
    for addr in watch_list:
        try:
            new_updates.append(eth.get_erc20_token_transfer_events_by_address(addr, last_block, 'latest', 'desc'))
        except AssertionError:
            continue
    if len(new_updates) > 0:
        last_block = int(new_updates[0][0]['blockNumber'])
    for update in new_updates:
        for txn in update:
            await client.message.channel.send(f"Transfer from {ensName(txn['from'])} to {ensName(txn['to'])} of {float(txn['value'])/(10**int(txn['tokenDecimal']))} {txn['tokenSymbol']} on Ethereum")
    return last_block

@client.event
async def on_message(message):
  if message.content.startswith('$watch'):
    watch_list.append(message.content[7:])
    await message.channel.send(watch_list)

@tasks.loop(seconds=120)
async def watch(start_block):
    last_block = start_block
    last_block = await getLatestTxn(last_block)

watch.start(eth.get_block_number_by_timestamp(int(time.time()), "before"))
client.run(os.environ["DISCORD_TOKEN"])
