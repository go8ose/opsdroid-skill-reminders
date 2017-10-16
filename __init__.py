from opsdroid.matchers import match_regex
from opsdroid.matchers import match_crontab
from opsdroid.message import Message
import logging

from datetime import datetime, timedelta, timezone


@match_regex(r'^remind')
async def remember_something(opsdroid, config, message):
    store = await opsdroid.memory.get("reminders")
    if store == None:
        future_reminders = []
    else: 
        future_reminders = store['reminders']

    # TODO: parse the message to work out when the user wants to be
    # reminded, instead of just reminding them later on.
    now = datetime.now(timezone.utc)
    future_timestamp = now + timedelta(0,60)

    # TODO: parse the message to work out who should be reminded.

    # TODO: parse the message to work out what that person should be
    # reminded about.
    
    # Store timestamp as a float, to avoid problems with datetime being
    # represented in the the memory store.
    f_ts = future_timestamp.timestamp()

    # TODO: submit a PR to opsdroid core to have a way to uniquely identify
    # connectors with a string that can be stored in the memory.  Then use
    # that way. Currently if a bot has multiple slack connectors this
    # current scheme won't work.
    connector = message.connector.name

    future_reminders.append({
        'timestamp': f_ts,
        'message': 'At {} you asked for a reminder.  This is that reminder'.format(now),
        'user': message.user,
        'room': message.room,
        'connector': connector,
    })
    await opsdroid.memory.put('reminders', {
        'reminders': future_reminders,
        'last_updated': now.timestamp(),
        })
    await message.respond("Ok, I can do that.")



@match_crontab('* * * * *')
async def send_reminders(opsdroid, config, message):

    now = datetime.now(timezone.utc)
    store = await opsdroid.memory.get("reminders")
    remaining_reminders = []
    if store != None:
        for reminder in store['reminders']:
            try:
                reminder_timestamp = datetime.fromtimestamp(float(reminder['timestamp']), timezone.utc)
            except TypeError as e:
                logging.warning("Failed to convert timestamp: {}".format(reminder['timestamp']))
                continue
            if reminder_timestamp < now:
                try:
                    user = reminder['user']
                    room = reminder['room']
                    connector_name = reminder['connector']
                except KeyError as e:
                    logging.warning("Didn't find attributes expected in reminders memory: {}".format(e))
                    continue

                # Work out which connector to use
                connectors = [c for c in opsdroid.connectors if c.name == connector_name]
                if len(connectors) != 1:
                    logging.warning("Had trouble finding connector {}".format(connector_name))
                    continue

                connector = connectors[0]
                message = Message("", reminder['user'], reminder['room'], connector)
                await message.respond(reminder['message'])
            else:
                remaining_reminders.append(reminder)

        await opsdroid.memory.put('reminders', {
            'reminders': remaining_reminders,
            'last_updated': now.timestamp(),
        })

