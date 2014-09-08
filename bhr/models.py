from django.contrib.auth.models import User
from django.db import models

from netfields import CidrAddressField

from django.utils import timezone

class WhitelistError(Exception):
    pass

def is_whitelisted(cidr):
    for item in WhitelistEntry.objects.all():
        if cidr in item.cidr:
            return item
    return False

class WhitelistEntry(models.Model):
    cidr = CidrAddressField()
    who = models.ForeignKey(User, editable=False)
    why = models.TextField()
    added = models.DateTimeField('date added', auto_now_add=True)

class CurrentBlockManager(models.Manager):
    def get_queryset(self):
        return super(CurrentBlockManager, self).get_queryset().filter(
            blockentry__removed__isnull=True)

FLAG_NONE     = "N"
FLAG_INBOUND  = "I"
FLAG_OUTBOUND = "O"
FLAG_BOTH     = "B"

class Block(models.Model):

    FLAG_DIRECTIONS = (
        (FLAG_NONE, 'None'),
        (FLAG_INBOUND, 'Inbound'),
        (FLAG_OUTBOUND, 'Outbound'),
        (FLAG_BOTH, 'Both'),
    )

    cidr = CidrAddressField()
    who  = models.ForeignKey(User, editable=False)
    source = models.CharField(max_length=30)
    why  = models.TextField()

    added = models.DateTimeField('date added', auto_now_add=True)
    unblock_at = models.DateTimeField('date to be unblocked', null=True)

    flag = models.CharField(max_length=1, choices=FLAG_DIRECTIONS, default=FLAG_NONE)

    skip_whitelist = models.BooleanField(default=False)

    forced_unblock  = models.BooleanField(default=False)
    unblock_why = models.TextField(blank=True)

    objects = models.Manager()
    current = CurrentBlockManager()

    def save(self, *args, **kwargs):
        if not self.skip_whitelist:
            wle = is_whitelisted(self.cidr)
            if wle:
                raise WhitelistError(wle.why)
        super(Entry, self).save(*args, **kwargs)


class BlockEntry(models.Model):
    entry = models.ForeignKey(Block)
    ident = models.CharField("blocker ident", max_length=50)

    added   = models.DateTimeField('date added', auto_now_add=True)
    removed =  models.DateTimeField('date removed', null=True)

    class Meta:
        unique_together = ('entry', 'ident')

    def set_unblocked(self):
        self.removed = timezone.now()

class BHRDB(object):
    def __init__(self):
        pass

    def current(self):
        return Block.current

    def get_block(self, cidr):
        """Get an existing block record"""
        return Block.current.filter(cidr=cidr).first()

    def add_block(self, cidr, who, source, why, unblock_at, duration):
        if duration:
            unblock_at = timezone.now() + datetime.timedelta(seconds=duration)

        b = Block(cidr=cidr, who=who, source=source, why=why, unblock_at=unblock_at)
        b.save()
        return b

    def set_blocked(self, cidr, ident):
        b = self.get_block(cidr)
        return b.blockentry_set.create(ident=ident)

    def set_unblocked(self, cidr, ident):
        b = self.get_block(cidr)
        b = b.blockentry_set.get(ident=ident)
        b.set_unblocked()
        b.save()

    def set_unblocked_by_id(self, block_id):
        b = BlockEntry.objects.get(pk=block_id)
        b.set_unblocked()
        b.save()