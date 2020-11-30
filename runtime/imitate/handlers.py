import kopf


@kopf.on.create('digi.dev', 'v1', 'mockrooms')
def create_fn(spec, **kwargs):
    print(f"And here we are! Creating: {spec}")
    return {'message': 'hello world'}  # will be the new status


@kopf.on.update('digi.dev', 'v1', 'mocklamps')
def update_fn(spec, **kwargs):
    print(f"And here we are! Updating: {spec}")
    return {'message': 'hello world'}  # will be the new status
