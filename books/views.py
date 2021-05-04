import json
import requests
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from .models import Book, Rating, Review, Illustration, User
from .forms import ReviewForm, BookForm, EditBookForm, ProtectionForm

def index(request):
	Books = Book.objects.all().order_by('id')
	return render(request, "books/index.html", {
		"Books": Books
		})

def login_view(request):
	if request.method == 'POST':
		username = request.POST["username"]
		password = request.POST["password"]

		user = authenticate(request, username=username, password=password)

		if user is not None:
			login(request, user)
			return HttpResponseRedirect(reverse("index"))
		else:
			return render(request, "books/login.html", {
			"message": "Invalid username and/or password."
			})
	else:
		return render(request, "books/login.html")

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
			return render(request, "books/register.html", {
			"message": "Passwords must match."
			})

		# Attempt to create new user
		try:
			user = User.objects.create_user(username, email, password)
			user.save()

		except IntegrityError:
			return render(request, "books/register.html", {
			"message": "Username already taken."
			})
		login(request, user)
		return HttpResponseRedirect(reverse("index"))
	else:
		return render(request, "books/register.html")

def book(request, book_id):
	book = get_object_or_404(Book, id=book_id)
	if request.method == "POST":
		if request.user.is_superuser:
			form = ProtectionForm(request.POST)
			if form.is_valid():
				book.protection = form.cleaned_data["protection"]
				book.save()
				return HttpResponseRedirect(reverse("book", args=[book.id]))
		else:
			return HttpResponseRedirect(reverse("book", args=[book.id]))

	else:
		# Get book illustrations and reviews objects
		illustrations = Illustration.objects.filter(book=book)
		reviews = Review.objects.filter(book=book)

		context = {
			"Book": book,
			"Illustrations": illustrations,
			"Reviews": reviews,
			"ProtectionForm": ProtectionForm()
		}
		# Show user rating if exists
		if request.user.is_authenticated and Rating.objects.filter(user=request.user, book=book).exists():
			rating = Rating.objects.get(user=request.user, book=book)
			context["rating_score"] = rating.score
			return render(request, "books/book.html", context)
		else:
			return render(request, "books/book.html", context)

@login_required
def contribute(request):
	if request.method == "POST":
		form = BookForm(request.POST, request.FILES)
		if form.is_valid():
			book = form.save()
			user = User.objects.get(username=request.user.username)
			user.contributions += 1
			user.save()
			print(user.contributions)

			return HttpResponseRedirect(reverse("book", args=[book.id]))
		else:
			return render(request, "books/contribute.html", {
				"form": form
				})
	else:
		initial_data = {
			"isbn": {"isbn10": "Insert ISBN10 here", "isbn13": "Insert ISBN13 here"},
			"genres": {"genres": ["insert", "genres", "here"]},
			"characters": {"characters": ["Insert", "characters", "here"]},
			"keywords": {"keywords": ["Insert", "keywords", "here"]},
		}
		return render(request, "books/contribute.html", {
			"form": BookForm(initial=initial_data)
			})

def edit_book(request, book_id):
	book = get_object_or_404(Book, id=book_id)
	if request.method == "POST":
		form = EditBookForm(request.POST, instance=book)
		if form.is_valid():
			edit_book = form.save()
			user = User.objects.get(username=request.user.username)
			user.contributions += 1
			user.save()
			print(user.contributions)

			return HttpResponseRedirect(reverse("book", args=[book.id]))
		else:
			return render(request, "books/edit_book.html", {
				"form": form
				})
	else:
		return render(request, "books/edit_book.html", {
			"form": EditBookForm(instance=book),
			"book_id": book.id
			})

def get_book(request, book_id):
	book = get_object_or_404(Book, id=book_id)
	print(book.genres)
	return JsonResponse({"book": {"title": book.title, "author": book.author,
						 "synopsis": book.synopsis, "cover": book.book_cover.url,
						 "genre": book.genres["genres"][0] }})

def search_book(request):
	pass

def rate_book(request):
	if request.user.is_authenticated:
		if request.method == 'POST':
			data = json.loads(request.body)
			rating_score = data.get('rating')

			#Get book object
			book_id = data.get('book_id')
			book = get_object_or_404(Book, id=book_id)

			# Get rating object and insert score, create if dont exist
			try:
				rating = Rating.objects.get(user=request.user, book=book)
				rating.score = rating_score
				rating.save()
			except ObjectDoesNotExist:
				rating = Rating(book=book, user=request.user, score=rating_score)
				rating.save()

			return JsonResponse({'success':'true', 'score': rating_score}, safe=False)

		if request.method == "DELETE":
			data = json.loads(request.body)
			#Get book object
			book_id = data.get('book_id')
			book = get_object_or_404(Book, id=book_id)
			try:
				rating = Rating.objects.get(user=request.user, book=book)
				rating.delete()
				return JsonResponse({'success':'deleted'})
			except ObjectDoesNotExist:
				return JsonResponse({'error':'rating dont exist!'})
	else:
		return JsonResponse({'error':'login_required'})

@login_required
def illustration(request, book_id):
	book = get_object_or_404(Book, id=book_id)
	if request.method == "POST":
		for i in request.FILES.values():
			illustration = Illustration(book=book, image=i)
			illustration.save()

		return HttpResponseRedirect(reverse("book", args=[book_id]))

	if request.method == "DELETE":
		data = json.loads(request.body)
		print(data)
		for i in data:
			illustration = get_object_or_404(Illustration, id=i)
			illustration.delete()

		return JsonResponse({'success':'deleted'})

	else:
		illustrations = Illustration.objects.filter(book=book)
		return render(request, "books/illustration.html", {
			"book_id": book.id,
			"book_title": book.title,
			"illustrations": illustrations
			})

@login_required
def review_book(request, book_id):
	book = get_object_or_404(Book, id=book_id)
	context = {
		"book": book
	}
	# Prevent review duplication
	if Review.objects.filter(user=request.user, book=book).exists():
		return HttpResponseRedirect(reverse("edit_review", args=[book_id]))

	if request.method == "POST":
		# Prevent review duplication
		if Review.objects.filter(user=request.user, book=book).exists():
			return JsonResponse({'error':'review already exists!'})

		form = ReviewForm(request.POST)
		if form.is_valid():
			rating = form.cleaned_data['rating']
			title = form.cleaned_data["title"]
			text = form.cleaned_data["text"]
			
			review = Review(user=request.user, book=book, title=title, text=text, score=rating)
			review.save()

			return HttpResponseRedirect(reverse("book", args=[book_id]))
		else:
			context["message"] = "Invalid input"
			return render(request, "books/review.html", context)
	else:
		return render(request, "books/review.html", context)

@login_required
def edit_review(request, book_id):
	book = get_object_or_404(Book, id=book_id)
	if request.method == "POST":
		try:
			review = Review.objects.get(user=request.user, book=book)
			form = ReviewForm(request.POST)
			if form.is_valid():
				rating = form.cleaned_data['rating']
				title = form.cleaned_data["title"]
				text = form.cleaned_data["text"]
				review.score = rating
				review.title = title
				review.text = text
				review.save()
				return HttpResponseRedirect(reverse("book", args=[book_id]))
			else:
				return render(request, "books/review.html", {
				"book": book,
				"message": "Invalid input"
				})
		except ObjectDoesNotExist:
			return HttpResponseRedirect(reverse("book", args=[book_id]))
	else:
		try:
			review = Review.objects.get(user=request.user, book=book)
		except ObjectDoesNotExist:
			return HttpResponseRedirect(reverse("book", args=[book_id]))

		return render(request, "books/edit_review.html", {
			"book": book,
			"review": review
			})