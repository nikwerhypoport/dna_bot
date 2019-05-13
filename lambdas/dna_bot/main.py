import json


def is_valid(signature):
    # validate against secret
    return True


def branch_creation_handler(event, context):

    content = event.get('body')
    print(content)

    signature = event.get('headers',{}).get('X-Hub-Signature')
    print(signature)

    if is_valid(signature):
        print('ok')

    # print(event)
    #print(json.dumps(event, indent=False))