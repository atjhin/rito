from enum import Enum

class Comm(Enum):
    SEQ = "sequential"
    RAN = "random"

class PastHistory(Enum):
    Trimmer = "trimmer"
    Summarizer = "summarizer"