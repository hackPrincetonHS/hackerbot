import os
import time
import re
from slackclient import SlackClient
import datetime
import twitter
import facebook
import json
'''
Built by Lincoln Roth for hackPHS
Origianally built 2/12/2018

hackerbot is a slack bot for running hackathons
'''
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))#needs slack bot token generated for your bot
twitterapi = twitter.Api(consumer_key=os.environ.get('TWITTER_CONSUMER_KEY'),#needs twitter consumer key for your twitter account
                      consumer_secret=os.environ.get('TWITTER_CONSUMER_SECRET'),#needs twitter consumer secret key for your twitter account
                      access_token_key=os.environ.get('TWITTER_ACCESS_TOKEN_KEY'),#needs twitter access token key for your twitter account
                      access_token_secret=os.environ.get('TWITTER_ACCESS_TOKEN_SECRET'))#needs twitter access token secret key for your twitter account
hackerbot_id = None#starts off as none, but it will get assigned later

cfg = {
"page_id"      : os.environ.get("FB_PAGE_ID"),  # Page id from the about section on your fb page
"access_token" : os.environ.get("FB_PAGE_ACCESS_TOKEN")   # From GraphAPI
}
admins = []#list of admins, soon to be replaced with json
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "help"#example command for when user enters something not related
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"#Regular expression to determine whether hackerbot was mentioned
eventnames = ["hackPHS 2018"]#phasing out
eventtimes = [datetime.datetime(2018, 10, 6, 10)]#phasing out
privatechannelnames = ["organizers", "mentors", "sponsorship", "logistics", "outreach", ]#names of all the private channels hackerbot is in, since it cannot find them in channels.list
privatechannelids = ["G8X0JFDDW", "G97J8D6GM", "G8X0JL256", "G97NNTC5T", "G8XP81HTP"]#ids of all the private channels hackerbot is in, since it cannot find them in channels.list

def get_api(cfg):
  graph = facebook.GraphAPI(cfg['access_token'])
  resp = graph.get_object('me/accounts')
  page_access_token = None
  for page in resp['data']:
    if page['id'] == cfg['page_id']:
      page_access_token = page['access_token']
  graph = facebook.GraphAPI(page_access_token)
  return graph

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.

    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == hackerbot_id:
                return message, event["channel"], event["user"]
    return None, None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel, user):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Sorry, I don't know that. Try *How long until hackPHS*"



    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if user in admins:#Checks if user is an admin
        if command.lower().startswith("twitter"):
            status = twitterapi.PostUpdate(command[8:])
            response = "Posted " + command[8:] + " to twitter!"
        if command.lower().startswith("facebook"):
            api = get_api(cfg)
            msg = command[9:]
            status = api.put_wall_post(msg)
            response = "Posted " + command[9:] + " to facebook!"
        if command.lower().startswith("socialfbt"):
            status = twitterapi.PostUpdate(command[8:])
            api = get_api(cfg)
            msg = command[10:]
            status = api.put_wall_post(msg)
            response = "Posted " + command[10:] + " to facebook and twitter!"
        if command.lower().startswith("tell"):
            channels = slack_client.api_call("channels.list")
            userlist = slack_client.api_call("users.list")
            # print("users", userlist)
            # print(channels["channels"])
            #check private ones now
            # print(command)
            for i in privatechannelnames:


                if i in command:
                    response = command[command.index(i)+len(i):]
                    channel = privatechannelids[privatechannelnames.index(i)]
                    break

            for i in channels["channels"]:
                print(i["name"])
                print(command)
                if i["name"] in command:
                    print(command.index(i["name"]))
                    response = command[command.index(i["name"])+len(i["name"]):]
                    channel = i["id"]
                    break

            for i in userlist["members"]:
                print(i["real_name"])
                if i["real_name"] in command:
                    response = command[command.index(i["real_name"])+len(i["real_name"]):]
                    channel = i["id"]
                    print(response)
                    print("KJSDFKJLSDF", i["real_name"])
                    print(channel)
                    break


        if command.lower().startswith("tell the organizers"):#tells hackerbot message to organizers channel
            response = command[20:]
            channel = "G8X0JFDDW"
        if command.lower().startswith("make announcement: "):#tells hackerbot message to general channel
            response = command[19:]
            channel = "C8XBQ773M"
        if command.lower() == "who are the organizers":#prints out all organizers (mainly for testing)
            response = "The hackPHS 2018 organizers are "
            for i in admins:
                response += "<@{}>".format(i) + " "
        if command.lower() == "who wrote hackerbot":#because I'm egotistical
            response = "<@U8YACG4MU>, if you have any questions, please dm him"
        if command.lower() == "help":#help NEEDS IMPROVED DOCUMENTATION LATER
            response = "hackerbot is here to help! Ask me a question and I'll try to answer."
        if command.lower() == "hi" or command.lower() == "howdy" or command.lower() == "hello":#Howdy!
            response = "Howdy <@{}>".format(user)


    if command.lower() == "thanks":
        response = "You're very welcome!"

    if "make me an admin" in command:
        admins.append(user)
        response = "You are now an admin!"
    if "mentor" in command:
        if command.lower().startswith("mentor:"):
            response="Great, a mentor will contact you as soon as one is available"
            slack_client.api_call(
                "chat.postMessage",
                channel="G97J8D6GM",
                text="<@{}>".format(user) + " needs help with \"" + command[7:] + "\""
            )
        else:
            response = "If you need a mentor, please ask hackerbot in the the form mentor: what you need help with"
    if command.lower() == "who wrote hackerbot":
        response = "<@U8YACG4MU>, if you have any questions, please dm him"
    if "when is" in command:
        response = whenIs(command)
    if command.lower().startswith("how long until "):
        response = timeUntil(command)
    if command.lower() == "help":
        response = "Hackerbot is here to help! Ask me a question and I'll try to answer. Try *How long until hackPHS*"
    if command.lower() == "hi" or command.lower() == "howdy" or command.lower() == "hello":
        response = "Howdy <@{}>".format(user)
    if command.lower() == "thanks":
        response = "You're very welcome!"
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

def whenIs(command):
    event_data = open('events.json')

    events = json.load(event_data)
    for i in events["events"]:
        print(i["name"])

    for i in events["events"]:
        if i["name"] in command.lower():
            return (i["name"] + " is happening on " + i["date"] + " at " + i["time"])
    if "hackPHS 2018" in command:
        return "hackPHS will be returning October 6-7! Stay updated by visiting <http://hackphs.tech>"

def timeUntil(command):
    print('howdy')
    event_data = open('events.json')

    events = json.load(event_data)
    event = command[15:]
    for i in events["events"]:
        if i["name"] in event.lower():
            date = i["date"].split('-')
            year = int(date[0])
            month = int(date[1])
            day = int(date[2])
            time = i["time"].split(':')
            hour = int(time[0])
            minute = int(time[1])
            time = datetime.datetime(year, month, day, hour, minute)
            print(time)
            print(time)
            print(event)
            response = time - datetime.datetime.now()
            seconds = response.seconds
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            response = str(response.days) + " days, "+ str(h) + " hours, "+ str(m) + " minutes, and "+ str(s) + " seconds"
            return response

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Hacker Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        hackerbot_id = slack_client.api_call("auth.test")["user_id"]

        while True:
            reading = slack_client.rtm_read()
            print(parse_bot_commands(reading))
            command, channel, user = parse_bot_commands(reading)

            if command:
                handle_command(command, channel, user)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
