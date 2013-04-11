import re


COMMAND_HANDLED = True
COMMAND_NOT_HANDLED = None


class CommandException(Exception):
    def __init__(self, command_text, message=None, *args, **kwargs):
        super(CommandException, self).__init__(self, message, *args, **kwargs)
        self.command_text = command_text
        self.message = message

    def __str__(self):
        return "%s [%s]" % (self.message, self.command_text) if self.message else "Bad command: %s" % self.command_text


class UnknownCommandException(CommandException):
    pass


class CommandParser(object):
    """
    Entry point for parsing and executing game commands.
    """
    def parse(self, command_text, controller=None, user=None, world=None):
        """
        Parse the specified string and find the Command and match
        information that can handle it. Returns None if no known
        commands can handle it.
        """
        if command_text.startswith("/"):
            stripped = command_text[1:].strip()
            # Look for a subclass of Command whose format matches command_text
            for command_type in Command.__subclasses__():
                if not hasattr(command_type, "command"):
                    raise Exception("Subclasses of Command must have a command attribute.")
                cmd_regex = command_type.command
                match = re.match(cmd_regex, stripped)
                if match:
                    instance = command_type(stripped, user, world, controller)
                    return instance, match
        return None

    def execute(self, command_text, controller=None, user=None, world=None):
        """
        Finds and executes the first command that can handle the specified
        string. If the command has a return value, that value is returned.
        If it does not, then COMMAND_HANDLED is returned. If no commands
        can handle the string, COMMAND_NOT_HANDLED is returned.
        """
        parsed = self.parse(command_text, controller=controller, user=user, world=world)
        if parsed:
            command, match = parsed
            # Pass matched groups to command.execute
            # ...but filter out "None" arguments. If commands
            # want optional arguments, they should use keyword arguments
            # in their execute methods.
            args = filter(lambda a: a is not None, match.groups())
            kwargs = {}
            for key, value in match.groupdict().iteritems():
                if value is not None:
                    kwargs[key] = value
            ret = command.execute(*args, **kwargs)
            if ret is None:
                return COMMAND_HANDLED
            else:
                return ret
        else:
            if command_text.startswith("/"):
                raise UnknownCommandException(command_text)
            return COMMAND_NOT_HANDLED


class Command(object):
    command = None
    help_text = None

    def __init__(self, command_text, user, world, controller):
        self.command_text = command_text
        self.user = user
        self.world = world
        self.controller = controller

    def execute(self, *args, **kwargs):
        pass


class GiveBlockCommand(Command):
    command = r"^give (\d+(?:\.\d+)?)\s*(\d+)?$"
    help_text = "give <block_id> [amount]: Give a specified amount (default of 1) of the item to the player"

    def execute(self, block_id, amount=1, *args, **kwargs):
        try:
            self.user.inventory.add_item(float(block_id), quantity=int(amount))
        except KeyError:
            raise CommandException(self.command_text, message="ID %s unknown." % block_id)
        except ValueError:
            raise CommandException(self.command_text, message="ID should be a number. Amount must be an integer.")


class SetTimeCommand(Command):
    command = r"^time set (\d+)$"
    help_text = "time set <number>: Set the time of day 00-24"

    def execute(self, time, *args, **kwargs):
        try:
            tod = int(time)
            if 0 <= tod <= 24:
                self.controller.time_of_day = tod
            else:
                raise ValueError
        except ValueError:
            raise CommandException(self.command_text, message="Time should be a number between 0 and 24")