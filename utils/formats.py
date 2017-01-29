async def entry_to_code(bot, entries):
    width = max(map(lambda t: len(t[0]), entries))
    output = ['```']
    fmt = '{0:<{width}}: {1}'
    for name, entry in entries:
        output.append(fmt.format(name, entry, width=width))
    output.append('```')
    await bot.say('\n'.join(output))


async def indented_entry_to_code(bot, entries, code='python'):
    width = max(map(lambda t: len(t[0]), entries))
    output = ['```{}'.format(code)]
    fmt = '\u200b{0:>{width}}: {1}'
    for name, entry in entries:
        output.append(fmt.format(name, entry, width=width))
    output.append('```')
    await bot.say('\n'.join(output))


def str_split(string, lang=""):
    if len(string) > 0:
        strings = [string[i:i + 1900] for i in range(0, len(string), 1900)]
        output = []
        for i in strings:
                output.append('```{}\n{}```'.format(lang, ''.join(i)))
        return output
    else:
        return [':ok_hand:']
