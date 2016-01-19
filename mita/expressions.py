"""
Jenkins has a full blown engine to expand expressions to meaningful
representations of labels.  There is no support for anything similar in Python,
so this module provides a very dumb/simple approach to attempt and interpret
these expressions into consumable data formats.

This has severe limitations, like not being able to parse nested grouping, but
it works wonders when the expression(s) is simple enough.
"""
import re


def generate_lists(op_split):
    results = []
    and_items = [i for i in op_split if 'and' in i]
    or_items = [i for i in op_split if 'or' in i]

    for item in and_items:
        if not results:
            results.append(item['and'])
        else:
            for r in results:
                r.extend(item['and'])

    for item in or_items:
        if not results:
            for i in item['or']:
                results.append([i])
        else:
            modified_results = []
            for count, r in enumerate(results):
                for i in item['or']:
                    new_combination = list(r)
                    new_combination.append(i)
                    modified_results.append(new_combination)
            results = modified_results

    # prune bad lists
    for count, item in enumerate(results):
        if len(item) != len(set(item)):
            results.pop(count)

    return results


def group_parse(parts):
    """
    Only used when parentheses are present in an expression, which then gets
    split into their own, so a bit more processing needs to happen, parsing
    individual portions as full-fledged expressions and later combining them
    """
    result = []
    for part in parts:
        result.extend(parse(part.split()))
    return result


def parse(parts):
    op_split = []
    current_split = []
    current_type = None
    previous = ''
    for count, part in enumerate(parts):
        if count == 0:
            previous = part
            current_split.append(part)
            continue

        if part == 'and':
            if current_type == 'or':
                # we've hit a change in operators
                op_split.append({'or': current_split})
                current_split = []
                current_split.append(previous)
            current_type = 'and'

        if part == 'or':
            if current_type == 'and':
                # we've hit a change in operators
                op_split.append({'and': current_split})
                current_split = []
                current_split.append(previous)
            current_type = 'or'

        if part not in ['or', 'and']:
            current_split.append(part)

        if count == len(parts)-1:
            # last one!
            op_split.append({current_type: current_split})

        previous = part

    return op_split


def translate(expression):
    """
    Replace the notation characters from label expressions into 'or' and 'and'
    """
    expression = expression.replace('&&', ' and ')
    return expression.replace('||', ' or ')


def expand(expression):
    """
    Given an expression statement, parse it and construct all possible
    combinations of it, returning a list of lists
    """
    expression = translate(expression)

    if '(' not in expression:
        # this is the easiest use case because it means we will just parse an
        # expression like `foo and bar and baz`
        parts = expression.split()
        op_split = parse(parts)
    else:
        parts = re.split(r'[()]', expression)
        parts = [i.strip() for i in parts if i]
        op_split = group_parse(parts)

    return generate_lists(op_split)
