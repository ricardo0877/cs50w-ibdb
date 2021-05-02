from django import forms
from books.models import Book, Illustration

CHOICES = [('1', '☆'),
		   ('2', '☆'),
		   ('3', '☆'),
		   ('4', '☆'),
		   ('5', '☆'),]

PROTECTIONS = [('no_protection', 'no_protection'),
			   ('pending_protection', 'pending_protection'),
			   ('semi_protection', 'semi_protection'),
			   ('extented_protection', 'extented_protection'),
			   ('template_protection', 'template_protection'),
			   ('full_protection', 'full_protection'),]

class ReviewForm(forms.Form):
	rating = forms.ChoiceField(choices=CHOICES)
	title = forms.CharField(max_length=175)
	text = forms.CharField(max_length=500)

class BookForm(forms.ModelForm):
	class Meta:
		model = Book
		exclude = ["protection"]

		widgets = {
            'synopsis': forms.Textarea(),
        }

class EditBookForm(forms.ModelForm):
	class Meta:
		model = Book
		exclude = ['book_cover', "protection"]

class ProtectionForm(forms.Form):
	protection = forms.ChoiceField(choices=PROTECTIONS)