import asyncio
import threading
import inspect
import traceback
import code
import sys


class asyncEval(object):
    def __init__(self, locals=None, loop=None):
        if locals is None:
            locals = {"__name__": "__console__", "__doc__": None}

        self.locals = locals
        self.loop = asyncio.get_event_loop() if loop is None else loop

    async def run(self, data):
        future = self.loop.run_in_executor(None, eval, data, self.locals)
        try:
            response = await future
            
            if inspect.isawaitable(response):
                response = await response
        except:
            response = traceback.format_exc()

        return response


class Repl(code.InteractiveConsole):

    """Interactive Python Console class"""

    def __init__(self, items=None, loop=None):
        if items is None:
            items = {}
        code.InteractiveConsole.__init__(self, items)
        self._buffer = ""
        self.result = None
        self.locals = items

    def write(self, data):
        self._buffer += str(data)

    def run(self, data):
        sys.stdout = self
        self.push(data)
        sys.stdout = sys.__stdout__
        result = self._buffer
        self._buffer = ""
        self.result = result

    def showtraceback(self):
        self._buffer += "{}".format(traceback.format_exc())

    def showsyntaxerror(self, *args):
        self.showtraceback()

    async def arun(self, data):
        repl_thread = threading.Thread(target=self.run, args=(data,))
        repl_thread.daemon = True
        repl_thread.start()

        while repl_thread.isAlive():
            await asyncio.sleep(.1)

        result = self.result

        if inspect.isawaitable(result):
            self.result = await result

        return self.result

async def subproc(command):
    create = asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    proc = await create

    await proc.wait()
    output = await proc.communicate()
    return output[0].decode()