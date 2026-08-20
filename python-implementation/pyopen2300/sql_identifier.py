"""Safe handling of PostgreSQL identifiers configured as schema.table."""

def table_identifier(table_name: str):
    """Split dots outside double quotes and return a composed identifier."""
    from psycopg2 import sql

    parts = []
    part = []
    quoted = False
    index = 0
    while index < len(table_name):
        character = table_name[index]
        if character == '"':
            part.append(character)
            if quoted and index + 1 < len(table_name) and table_name[index + 1] == '"':
                part.append('"')
                index += 1
            else:
                quoted = not quoted
        elif character == '.' and not quoted:
            parts.append(''.join(part).strip())
            part = []
        else:
            part.append(character)
        index += 1
    if quoted:
        raise ValueError(f'Unterminated quoted table identifier: {table_name}')
    parts.append(''.join(part).strip())
    if not parts or any(not part for part in parts):
        raise ValueError(f'Invalid table identifier: {table_name}')

    identifiers = []
    for part in parts:
        if part.startswith('"') or part.endswith('"'):
            if len(part) < 2 or not (part.startswith('"') and part.endswith('"')):
                raise ValueError(f'Invalid quoted table identifier: {table_name}')
            identifiers.append(part[1:-1].replace('""', '"'))
        else:
            identifiers.append(part)
    return sql.Identifier(*identifiers)
