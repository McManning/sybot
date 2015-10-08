import random

from sybot import app, mumble

# Test text message listener

@mumble.text('^!(?P<dice>\d+)d(?P<sides>\d+)'):
def roll(server, user, message, args):
    print('Roll!')
    print(server)
    print(user)
    print(message)
    print(args)

    dice = int(args.group("dice"))
    sides = int(args.group("sides"))

    if sides < 1:
        response = "How Can Dice Be Real If Their Sides Are Not?"
    elif dice < 1:
        response = "How Can Sides Be Real If Dice Are Not?"
    elif dice > 5:
        response = "I don't have that many dice."
    else:
        rolls = [str(random.randint(1, sides)) for x in range(dice)]
        response = "{} rolled {}".format(
            user.name,
            ", ".join(rolls)
        )

    server.sendMessageChannel(user.channel, 0, response)
    return True

# Eventually?
#@mumble.voice:
#def foo(server, user, payload?)

if __name__ == '__main__':
    mumble.connect()
    app.run(use_reloader=False)
