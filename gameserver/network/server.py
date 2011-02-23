from twisted.python import log
from twisted.internet import protocol
from twisted.application import service
from gameserver.network.protocol import JsonReceiver
from gameserver.game import Game, GameError

class GameProtocol(JsonReceiver):

    def __init__(self):
        self.game = Game()

    def connectionMade(self):
        peer = self.transport.getPeer()
        log.msg('Connection made from {0}:{1}'.format(peer.host, peer.port))

    def objectReceived(self, data):
        """Decodes and runs a command from the received data"""

        log.msg('Data received: {0}'.format(data))

        if not data.has_key('command'):
            self.sendError("Empty command")
            return

        command = data['command']
        params = data.get('params', {})

        self.runCommand(command, **params)

    def sendError(self, message):
        self.sendResponse('error', message=message)

    def sendResponse(self, command, **params):
        self.sendObject(command=command, params=params)
        log.msg('Data sent: {0}({1})'.format(command, params))

    #def connectionLost(self, reason=connectionDone):
    #    log.msg('Connection lost')

    def runCommand(self, command, **params):
        """
        Executes a command.

        Possible commands:

        - start([side=<x_or_o>]) - (re)start game
            x_or_o ("x", "X", "o" or "O") - which side the player chooses
            can be empty, in this case sides will be assigned randomly

        - move(x=<x>, y=<y>) - make move to a cell with coords x, y
            x (1..3) - Column number
            y (1..3) - Row number
        """

        commands = {
                    'start': self.game.startGame,
                    'move': self.makeMove,
                    }

        if not commands.has_key(command):
            self.sendError('Invalid command: "{0}"'.format(command))
            return

        try:
            commands[command](**params)
        except (ValueError, TypeError, GameError), e:
            self.sendError('Error executing command "{0}": {1}'.format(command, e))

    def makeMove(self, x, y):
        self.game.makeMove(x, y)
        self.sendResponse('move', x=x, y=y)


class GameFactory(protocol.ServerFactory):

    protocol = GameProtocol

    def __init__(self, service):
        self.service = service

class GameService(service.Service):
    pass
