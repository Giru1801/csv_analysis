import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

from django.shortcuts import render, redirect
from django.conf import settings
from .forms import FileUploadForm

def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save()
            request.session['file_path'] = file_instance.file.url
            return redirect('analyze_file')
    else:
        form = FileUploadForm()
    return render(request, 'analysis/upload.html', {'form': form})

def analyze_file(request):
    file_path = request.session.get('file_path')
    if not file_path:
        return redirect('upload_file')

    # Correct file path construction
    relative_path = file_path.replace(settings.MEDIA_URL, "").lstrip("/")
    file_absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    # Load CSV data
    try:
        data = pd.read_csv(file_absolute_path, encoding='utf-8')
    except UnicodeDecodeError:
        data = pd.read_csv(file_absolute_path, encoding='latin1')
    analysis_results = {
        'head': data.head().to_html(),
        'describe': data.describe().to_html(),
        'missing': data.isnull().sum().reset_index().to_html(header=['Column', 'Missing Values'], index=False),
    }

    # Generate histogram for numerical columns
    plot_path = os.path.join(settings.MEDIA_ROOT, 'analysis/plots/')
    os.makedirs(plot_path, exist_ok=True)
    plots = []

    for column in data.select_dtypes(include=['number']).columns:
        plt.figure()
        sns.histplot(data[column], kde=True)
        plot_filename = f"{column}_hist.png"
        plt.savefig(os.path.join(plot_path, plot_filename))
        plt.close()
        plots.append(f'/media/analysis/plots/{plot_filename}')

    return render(request, 'analysis/results.html', {
        'analysis_results': analysis_results,
        'plots': plots
    })