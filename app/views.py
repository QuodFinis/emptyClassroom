from django.urls import reverse

from django.shortcuts import redirect, render

from django.http import HttpResponse, JsonResponse

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from app.utils.upload_to_blob import upload_to_blob
from .models import UploadedFileStatus  # Model to track file processing

import logging
logger = logging.getLogger('app')


def index(request):
	return HttpResponse("Hello, world.")


def signup(request):
	if request.method == "POST":
		form = UserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password1')
			user = authenticate(username=username, password=password)
			login(request, user)
			return redirect('home')
		else:
			form = UserCreationForm()

		return render(request, 'signup.html', {'form': form})

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')

@login_required
def dashboard(request):
    return render(request, 'app/dashboard.html')


@login_required
def get_sas_url(request):
	from app.utils.generate_sas_url import generate_sas_url
	sas_url = generate_sas_url()
	return JsonResponse({'sas_url': sas_url})

@login_required
def upload_schedule(request):
	if request.method == 'POST' and request.FILES.get('file'):
		logger.debug("Received file upload request.")
		file = request.FILES['file']
		logger.debug(f"File received: {file.name}")

		if not file:
			logger.error("No file uploaded")
			return JsonResponse({'error': 'No file uploaded'}, status=400)

		if not file.name.endswith(('.xls', '.xlsx')):
			logger.warning(f"Invalid file type: {file.name}")
			return JsonResponse({'error': 'Invalid file type'}, status=400)

		try:
			logger.info(f"Uploading {file.name} to Azure Blob Storage...")
			status = upload_to_blob(file)

			return redirect(reverse('app:upload_status', args=[status]))

		except Exception as e:
			logger.exception("Error during file upload or processing:")
			return JsonResponse({'success': False, 'message': str(e)})

	logger.info("Rendering upload form.")
	return render(request, 'app/upload_schedule.html')

@login_required
def upload_status(request, status_id):
	status = UploadedFileStatus.objects.get(id=status_id)
	return JsonResponse({
		'status': status.status,
		'error_message': status.error_message
	})