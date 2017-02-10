import asyncio
import inspect
import traceback


class AsyncEval:
    def __init__(self, loop, locals=None, thread_pool=None):
        if locals is None:
            locals = {'__name__': '__console__', '__doc__': None}

        self.locals = locals
        self.loop = loop
        self.thread_pool = thread_pool

    async def run(self, data):
        future = self.loop.run_in_executor(self.thread_pool, eval, data, self.locals)
        try:
            response = await future
            
            if inspect.isawaitable(response):
                response = await response
        except:
            response = traceback.format_exc()

        return response


async def subproc(command):
    create = asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    proc = await create

    await proc.wait()
    output = await proc.communicate()
    return output[0].decode()
