import os
import time
import discord
from etherscan import Etherscan
from dotenv import load_dotenv
load_dotenv()

from web3.auto.infura import w3
from ens import ENS
from discord.ext import tasks

ns = ENS.fromWeb3(w3)
eth = Etherscan(os.environ['ETHERSCAN_API_KEY'])
watch_list = ['0x2d407ddb06311396fe14d4b49da5f0471447d45c']
client = discord.Client()


async def ensName(addr):
    ens = ns.name(addr)
    if ens is None:
        return addr
    else:
        return ens[0]


async def getLatestTxn(last_block):
    new_updates = []
    channel = client.get_channel(929862118407290880)
    for addr in watch_list:
        try:
            new_updates.append(eth.get_erc20_token_transfer_events_by_address(addr, last_block, 'latest', 'desc'))
        except AssertionError:
            continue
    if len(new_updates) > 0:
        last_block = int(new_updates[0][0]['blockNumber'])
    for update in new_updates:
        for txn in update:
            await channel.send(f"Transfer from {ensName(txn['from'])} to {ensName(txn['to'])} of {float(txn['value'])/(10**int(txn['tokenDecimal']))} {txn['tokenSymbol']} on Ethereum")
    return last_block


@client.event
async def on_message(message):
    if message.content.startswith('$watch'):
        if(w3.isAddress(message.content[7:])):
            watch_list.append(message.content[7:])


@tasks.loop(seconds=180)
async def watch(start_block):
    await client.wait_until_ready()
    last_block = start_block
    start_block = await getLatestTxn(last_block)


watch.start(eth.get_block_number_by_timestamp(int(time.time()), "before"))
client.run(os.environ["DISCORD_TOKEN"])
