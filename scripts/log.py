__author__ = "joaonrb"


import uuid
from datetime import datetime
from cqlengine import columns
from cqlengine.models import Model


class LogEntry(Model):
    read_repair_chance = 0.05  # optional - defaults to 0.1

    id = columns.UUID(primary_key=True)
    user = columns.Ascii()
    item = columns.Ascii()
    created_at = columns.DateTime(index=True)
    type = columns.Ascii()
    value = columns.Float(default=.0)

    @classmethod
    def create(cls, user=None, item=None, created_at=None, type=None, value=.0):
        created_at = created_at or datetime.utcnow()
        lid = uuid.uuid3(uuid.NAMESPACE_DNS, "%s:%s:%s" % (user, item, created_at))
        super(cls, LogEntry).create(id=lid, user=user, item=item, created_at=created_at, type=type, value=value)


"""
from cqlengine import connection
connection.setup(["Ana"], "cqlengine")
from cqlengine.management import sync_table
from log import LogEntry
sync_table(LogEntry)
#l0 = LogEntry.create(user="0077db7d5bcccd3a83a60acf9fc1f9f64293a0ad29e6f8548b9d29b3f9ae6d1d", item=123456, type="RECOMMEND")

#import click
import random
import numpy as np
from datetime import datetime
#with click.progressbar(xrange(8671875), length=8671875, label="Generating logs to Cassandra") as bar:
types = np.array([0]*80+[1]*15+[2]*4+[3])
np.random.shuffle(types)
users = np.array(xrange(75000))
items = np.array(xrange(8500))
types_map = ["RECOMMEND", "CLICK", "INSTALL", "REMOVE"]
for i in xrange(6):
    month = i + 6
    for day in xrange(1, 31):
        for t in (np.random.rand(random.randint(8666875, 8676875))*1440).astype(np.int32):
            min, sec = int(t/60), int(t%60)
            hour, min = int(min/24), int(min%24)
            created_at = datetime(year=2014, month=11, day=14, hour=hour, minute=min, second=sec)
            l = LogEntry.create(user=str(np.random.choice(users, 1)[0]), item=str(np.random.choice(users, 1)[0]),
                                type=types_map[np.random.choice(types, 1)[0]], created_at=created_at)
        print "%s-%s-2014 done!" % (day, month)
"""