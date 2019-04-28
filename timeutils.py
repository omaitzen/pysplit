def format_time(time, difference=False, full=True):
    if time is None:
        return ''
    elif time < 0:
        return '-' + format_time(-time, full=not difference)
    elif difference:
        return '+' + format_time(time, full=False)

    return (
        '{minutes:02d}:{seconds:02d}.{tenths}' if full else
        '{seconds}.{tenths}' if time < 60 else
        '{minutes}:{seconds:02d}.{tenths}'
    ).format(
        minutes=int(time) // 60,
        seconds=int(time) % 60,
        tenths=int(time * 10) % 10
    )


def parse_time(formatted):
    tokens = formatted.replace('.', ':').split(':')
    return int(tokens[0]) * 60 + int(tokens[1]) + (int(tokens[2]) / 10 if len(tokens) == 3 else 0)
