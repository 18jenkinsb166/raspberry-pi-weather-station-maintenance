import hashlib

# also a decorator. Calls the function repeatedly on the last result for multiple rounds of hashing


def repeat_decorator_factory(repeats: int):
    """works where there is one input and a process can be repeated by running again on previous output"""
    def decorator(function):
        name = function.__name__

        def wrapper(arg):
            result = arg
            for _ in range(repeats):
                result = function(result)
            return result
        wrapper.__name__ = name
        return wrapper
    return decorator

# function returns a hexadecimal string for the SHA256 hash of an object


@repeat_decorator_factory(10**3)
# @repeat_decorator_factory(1)
def hash(plain_txt):
    """one way hash using sha256"""
    hash_ = hashlib.sha256()
    hash_.update(plain_txt.encode())
    return hash_.hexdigest()


# local hash
with open("hashed_key.key", "r") as file:
    hashed_key = file.read()
# hashed_key.replace(chr(10), "").replace(" ", "").replace(chr(13), "")
hashed_key = hashed_key[:-1]

print(f"'{hashed_key}'")


print(f"'{hash(f'GqFpIvxfUt6Ku8CmtLVmdRzlS')}'")
assert hash("GqFpIvxfUt6Ku8CmtLVmdRzlS") == hashed_key
