"""Construct a fourth tile animation without modifying the source project."""
import copy


def add_ramadan_animation(data, image_path, image_size, animation_sid):
    if not isinstance(image_path, str) or not image_path.startswith('images/') or '..' in image_path:
        raise ValueError('invalid atlas path')
    if not isinstance(image_size, int) or image_size <= 0 or not isinstance(animation_sid, int) or animation_sid <= 0:
        raise ValueError('invalid atlas metadata')
    result = copy.deepcopy(data)
    animations = result['project'][3][5][7]
    if len(animations) == 4 and [a[0] for a in animations] == ['t0', 't1', 't2', 't3']:
        existing = animations[-1]
        if existing[6] != animation_sid or len(existing[7]) != 20 or any(
            f[0] != image_path or f[2:6] != [1+(i%5)*98, 1+(i//5)*98, 96, 96]
            for i, f in enumerate(existing[7])
        ):
            raise ValueError('unexpected existing Ramadan animation')
        animations.pop()
    if len(animations) != 3 or [a[0] for a in animations] != ['t0', 't1', 't2']:
        raise ValueError('unexpected tile animation set')
    def contains_sid(value):
        if isinstance(value, list): return any(contains_sid(item) for item in value)
        if isinstance(value, dict): return any(contains_sid(item) for item in value.values())
        return type(value) is int and value == animation_sid
    if contains_sid(result):
        raise ValueError('animation SID already in use')
    animation = copy.deepcopy(animations[0])
    animation[0] = 't3'
    animation[6] = animation_sid
    animation[7] = [[image_path, image_size, 1+(i%5)*98, 1+(i//5)*98, 96, 96, 1, .5, .5, [], [], 0] for i in range(20)]
    animations.append(animation)
    return result
