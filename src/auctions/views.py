from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.contrib.auth.decorators import login_required

from .models import User, Listing, Bid, Comment, Category

from djmoney.forms import MoneyField


def index(request):
    if request.user.is_authenticated:
        return render(request, "auctions/index.html", {
            "listings": Listing.objects.all(),
            "watchlist_len": len(request.user.watchlist.all())
        })
    else:
        return render(request, "auctions/index.html", {
            "listings": Listing.objects.all()
        })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    if request.user.is_authenticated:
        return render(request, "auctions/login.html", {
            "watchlist_len": len(request.user.watchlist.all())
        })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    if request.user.is_authenticated:
        return render(request, "auctions/register.html", {
            "watchlist_len": len(request.user.watchlist.all())
        })
    else:
        return render(request, "auctions/register.html")


class CreationForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "Title"}), max_length=120,
                            label='Title', required=True)
    # validators=[ RegexValidator('^[a-zA-Z1 ]*$', message='Please enter only alphabetical letters')]
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'columns': 3, 'placeholder': "Description"}), label='Description',
        max_length=5000, required=True)
    start_money = MoneyField(decimal_places=2, default_currency='USD', label='Starting bid',
                             currency_choices=[("USD", "$")], required=True, min_value=0,
                             max_value=1000000000)
    img = forms.ImageField(label='Image (optionally)', required=False)


@login_required
def create(request):
    categories = Category.objects.all()
    if request.method == "POST":
        forms = CreationForm(request.POST, request.FILES)
        if forms.is_valid():
            title = forms.cleaned_data["title"]
            description = forms.cleaned_data["description"]
            start_price = forms.cleaned_data["start_money"]
            image = forms.cleaned_data["img"]

            category = Category.objects.get(pk=int(request.POST["category"]))
            # Create the listing and save it
            bid = Bid.objects.create(initial_price=start_price, current_price=start_price)
            listing = Listing.objects.create(name=title, description=description, image=image, creator=request.user,
                                             price=bid)
            listing.categories.set([category])

            # listing = Listing(name=title, description=description, image=url, category='')
        else:
            return render(request, "auctions/create.html", {
                "creation_form": forms,
                "categories": categories,
                "watchlist_len": len(request.user.watchlist.all())
            })
    return render(request, "auctions/create.html", {
        "creation_form": CreationForm(),
        "categories": categories,
        "watchlist_len": len(request.user.watchlist.all())
    })


class BidForm(forms.Form):
    new_price = MoneyField(decimal_places=2, default_currency='USD', label='',
                           currency_choices=[("USD", "$")], required=True, min_value=0,
                           max_value=1000000000)
    new_price.widget.attrs['placeholder'] = 'Bid'


class CommentForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'columns': 5, 'placeholder': "Enter comment"}),
                           label='',
                           max_length=3000, required=True, min_length=1)


@login_required
def add_to_watchlist(request, index):
    if Listing.objects.filter(id=index).exists():
        lst = Listing.objects.get(id=index)
        if request.user in lst.watchlisters.all():
            lst.watchlisters.remove(request.user)
        else:
            lst.watchlisters.add(request.user)
    return HttpResponseRedirect(reverse("listing", args=(index,)))


@login_required
def close_listing(request, index):
    if Listing.objects.filter(id=index).exists():
        lst = Listing.objects.get(id=index)
        if request.user == lst.creator:
            # bid closing
            lst.is_closed = True
            lst.save()
    return HttpResponseRedirect(reverse("listing", args=(index,)))


@login_required
def like(request, index, comment_index):
    if Listing.objects.filter(id=index).exists():
        comments = Listing.objects.get(id=index).comment.all()
        if comments.filter(id=comment_index).exists():
            comment = comments.get(id=comment_index)
            if request.user in comment.likers.all():
                comment.likes_amount -= 1
                comment.likers.remove(request.user)
            else:
                comment.likes_amount += 1
                comment.likers.add(request.user)
            comment.save()
    return HttpResponseRedirect(reverse("listing", args=(index,)))

@login_required
def dislike(request, index, comment_index):
    if Listing.objects.filter(id=index).exists():
        comments = Listing.objects.get(id=index).comment.all()
        if comments.filter(id=comment_index).exists():
            comment = comments.get(id=comment_index)
            if request.user in comment.dislikers.all():
                comment.dislikes_amount -= 1
                comment.dislikers.remove(request.user)
            else:
                comment.dislikes_amount += 1
                comment.dislikers.add(request.user)
            comment.save()
    return HttpResponseRedirect(reverse("listing", args=(index,)))

def listing(request, index):
    watchlist_len = 0
    if request.user.is_authenticated:
        watchlist_len = len(request.user.watchlist.all())
    if Listing.objects.filter(id=index).exists():
        lst = Listing.objects.get(id=index)
        comments = lst.comment.all().order_by("-likes_amount", "dislikes_amount")
        # produce bidder
        bidder = "Your"
        if lst.current_bidder is not None and lst.current_bidder.username != request.user.username:
            bidder = lst.current_bidder.username + "\'s"

        if request.method == "POST":
            # bidding form
            bid_form = BidForm(request.POST)
            price_message = ""
            if bid_form.is_valid():
                bid = bid_form.cleaned_data['new_price']
                if bid > lst.price.current_price:
                    lst.price.current_price = bid
                    lst.price.bids_amount += 1
                    lst.current_bidder = request.user
                    lst.price.save()
                    lst.save()
                    price_message = "Bid successfully placed"
                else:
                    price_message = "The bid must be higher than the last bid"

            # comment form
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment_text = comment_form.cleaned_data['text']
                comm = Comment.objects.create(comment=comment_text, listing=lst,
                                              commentator=request.user)
                comm.save()

                return HttpResponseRedirect(reverse("listing", args=(index,)))
            else:
                return render(request, "auctions/listing.html", {
                    'listing': lst,
                    'index': index,
                    'bidder': bidder,
                    'bid_form': bid_form,
                    'price_message': price_message,
                    "watchlist_len": watchlist_len,
                    "is_creator": request.user == lst.creator,
                    "comment_form": comment_form,
                    "comments": comments
                })

        return render(request, "auctions/listing.html", {
            'listing': lst,
            'index': index,
            'bidder': bidder,
            'bid_form': BidForm(),
            'price_message': "",
            "watchlist_len": watchlist_len,
            "is_creator": request.user == lst.creator,
            "comment_form": CommentForm(),
            "comments": comments
        })
    else:
        return render(request, "auctions/noListing.html", {
            "watchlist_len": watchlist_len
        })


def categories(request):
    if request.user.is_authenticated:
        return render(request, "auctions/categories.html", {
            "categories": Category.objects.all(),
            "watchlist_len": len(request.user.watchlist.all())
        })
    else:
        return render(request, "auctions/categories.html", {
            "categories": Category.objects.all()
        })


def category(request, category_name):
    if Category.objects.filter(category=category_name).exists():
        ctg = Category.objects.get(category=category_name)
        if request.user.is_authenticated:
            return render(request, "auctions/category.html", {
                'category': ctg,
                'listings': Listing.objects.filter(categories=ctg).all(),
                "watchlist_len": len(request.user.watchlist.all())
            })
        else:
            return render(request, "auctions/category.html", {
                'category': ctg,
                'listings': Listing.objects.filter(categories=ctg).all()
            })
    else:
        if request.user.is_authenticated:
            return render(request, "auctions/noCategory.html", {
                "watchlist_len": len(request.user.watchlist.all())
            })
        else:
            return render(request, "auctions/noCategory.html")


@login_required
def watchlist(request):
    return render(request, "auctions/watchlist.html", {
        "listings": list(reversed(request.user.watchlist.all())),
        "watchlist_len": len(request.user.watchlist.all())
    })
