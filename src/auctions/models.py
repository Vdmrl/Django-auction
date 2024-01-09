from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from djmoney.models.fields import MoneyField


class User(AbstractUser):
    pass


class Category(models.Model):
    category = models.CharField(max_length=120)
    image = models.ImageField(null=True, default=None)
    description = models.TextField(max_length=500, null=True, default=None)

    def __str__(self):
        return self.category


class Bid(models.Model):
    initial_price = MoneyField(max_digits=13, decimal_places=2, default_currency="USD", default=0)
    current_price = MoneyField(max_digits=13, decimal_places=2, default_currency="USD", default=0)
    bids_amount = models.IntegerField(default=0)

    def __str__(self):
        return f"current price: {self.current_price} initial price: {self.initial_price}"


class Listing(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(max_length=5000)
    price = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name="cost")
    image = models.ImageField()
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="creator")
    creation_date = models.DateTimeField(default=timezone.now)
    categories = models.ManyToManyField(Category, blank=True, related_name="listings")
    current_bidder = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, default=None,
                                       related_name="bidder")
    watchlisters = models.ManyToManyField(User, blank=True, related_name="watchlist")
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        if self.image:
            return f"name: {self.name} with image, description: {self.description}, {self.price} by {self.creator} in {self.creation_date}. Category: {self.categories}"
        else:
            return f"name: {self.name} without image, description: {self.description}, {self.price} by {self.creator} in {self.creation_date}. Category: {self.categories}"


class Comment(models.Model):
    listing = models.ForeignKey(Listing, blank=False, on_delete=models.DO_NOTHING, related_name="comment", default=None)
    commentator = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="commentator")
    comment = models.TextField(max_length=3000)
    creation_date = models.DateTimeField(default=timezone.now)  # default
    likes_amount = models.IntegerField(default=0)  # default
    dislikes_amount = models.IntegerField(default=0)  # default
    likers = models.ManyToManyField(User, blank=True, default=None, related_name="likes")
    dislikers = models.ManyToManyField(User, blank=True, default=None, related_name="dislikes")


    def __str__(self):
        return f"{self.comment} by {self.commentator}"
