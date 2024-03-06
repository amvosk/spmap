

from pydantic import BaseModel


class ControlData(BaseModel):
    signal: str
    att: int
    dsfasdg: float

if __name__ == '__main__':
    cd = ControlData(signal='abc', att=1, dsfasdg=5.7)
    print(cd.__class__.__name__)
    for k, v in vars(cd).items():
        print(k, v)