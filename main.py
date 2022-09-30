import discord
from key import key
import asyncio
import random
import sys


lst = ["guac", "No_test"]

client = discord.Client()

@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name, client.user.id)


@client.event
async def on_message(msg):

    if msg.content.startswith("!count"):
        counter = 0
        temp = "Calculating messages..."
        async for log in msg.channel.history():
            if log.author == msg.author:
                counter += 1

        await msg.channel.send(temp + " In the past 100 messages, you have sent {}.".format(counter))


    elif msg.content.startswith("!sleep"):
        await msg.channel.send( "good night")
        await asyncio.sleep(5)
        await msg.channel.send( "good morning")


    elif msg.content.startswith("!rng"):
        await msg.channel.send( str(int(random.random()*100)))


    elif msg.content == "kys" and msg.author.name == "fall":
        await msg.channel.send( "ok i die")
        sys.exit()


    elif msg.content.startswith("hi") or msg.content.startswith("Hi") or msg.content.startswith("hey") or msg.content.startswith("Hey") or msg.content.startswith("$greet"):
        if msg.author.bot: return
        await msg.channel.send( "no one prompted you to speak so you can just stay quiet")


    elif msg.content == "big gay":
        await msg.channel.send( "no u")


    elif msg.content == "!who":
        await msg.channel.send( "i am the overlord, sir/madam {}".format(msg.author.name))


    elif msg.content == ("rock") or msg.content == ("paper") or msg.content == ("scissors"):
      if msg.author.bot: return
        
      ans = (random.random())
      print(ans)
      if ans < 0.33:
          await msg.channel.send("tbot picks rock")
      elif ans < 0.66 and ans > 0.33:
          await msg.channel.send("tbot picks scissors")
      elif ans > 0.66:
          await msg.channel.send("tbot picks paper")


    elif msg.content == "tcommands":
      await msg.channel.send("Current available commands include: \n!count - counts the amount of messages you have sent in the past 100. \n!cleanbot - deletes past messages sent by tbot. \n!cleanme - deletes past messages sent by you. \n!sleep - puts the bot to sleep for 5 seconds. \n!rng - generates a randon integer between 1-100. \n!who - who am i? \nrock, paper, scissors - play a game of rock paper scissors with tbot.")


    elif msg.content.startswith("!cleanbot"):
      print("deleting messages sent by tbot")
      def is_me(m):
          return m.author == client.user
      
      deletedme = await msg.channel.purge(limit=100, check=is_me)
      await msg.channel.send("deleted {} message(s) sent by tbot".format(len(deletedme)), delete_after=2)
      await asyncio.sleep(2)
      await msg.delete()


    elif msg.content.startswith("!cleanme"):
      print("deleting messages sent by user")
      def is_you(u):
          return u.author == msg.author

      deletedyou = await msg.channel.purge(limit=100, check=is_you)
      await msg.channel.send("deleted {} message(s) sent by user".format(len(deletedyou)), delete_after=2)
      await asyncio.sleep(2)
      await msg.delete()


    elif len(msg.content) > 0 and not msg.author.bot:
      for word in lst:
          if word in msg.content:
            print("bad word detected")
            await msg.channel.send( "Hey! nO pRoFaNiTy in my christian channel!! >:(")
            await msg.delete()
            await msg.channel.send( "@{} sent a bad message: ".format(msg.author.name) + msg.content)


client.run("key")

# invite link
# https://discord.com/api/oauth2/authorize?client_id=393195984122806272&permissions=43072&scope=bot%20applications.commands