from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, Context
from django.template.context import RequestContext
from rancho.project.models import Project
from rancho.chat.forms import ChatForm, LogForm
from rancho.chat.models import Post, ChatData

@login_required
def general_chat(request, p_id):
    SUMMARY_NUMBER = 15
    user = request.user
    project = get_object_or_404(Project, id=p_id)
    
    project.check_user_in_project_or_404(user)
    
    posts = Post.objects.filter(project = project)
    
    try:
        chat_data = ChatData.objects.get(project = project, user = user)
    except ChatData.DoesNotExist:
        chat_data = ChatData(user = user, project = project, last_request = -1)
        chat_data.save()
    chat_data.is_connected = True;
    chat_data.save()
    
    chat_form = ChatForm()
    
    recent_log = list(Post.objects.filter(project = project, date__lt = datetime.now()).order_by('date'))[-SUMMARY_NUMBER:]
    
    context = {'posts': posts, 'project': project, 'chat_form': chat_form, 'recent_log': recent_log}
    
    return render_to_response("chat/general.html", context, 
                              context_instance = RequestContext(request))

@login_required
def send_message(request, p_id):
    user = request.user
    project = get_object_or_404(Project, id = p_id)
    
    project.check_user_in_project_or_404(user)
    
    if request.method == 'POST':
        message = request.POST.get('message')
        if not message:
            return
        new_post = Post(author = user,
                        date = datetime.now(),
                        project = project,
                        message = message)
        new_post.save()
        
    return HttpResponse('', mimetype='text/html')


@login_required
def get_and_display_messages(request, p_id):
    def get_messages(request, p_id):
        SUMMARY_NUMBER = 15
        user = request.user
        project = get_object_or_404(Project, id = p_id)
        
        project.check_user_in_project_or_404(user)
        
        date = datetime.now()
        try:
            chat_data = ChatData.objects.get(user = user, project = project)
        except ChatData.DoesNotExist:
            chat_data = ChatData(user = user, project = project, last_request = -1, is_connected = True)
            chat_data.save()
        posts = []
        if chat_data:
            posts = Post.objects.filter(project = project, id__gt = chat_data.last_request).order_by('date')
        else:
            posts = Post.objects.filter(project = project).order_by('-date')[-SUMMARY_NUMBER:]
        chat_data.last_request = posts[len(posts)-1].id
        chat_data.is_connected = True 
        chat_data.save()
        return posts
    
    posts = get_messages(request, p_id)
    result = ''
    for post in posts:
        contents = '''{% load displaychatline %}
                      {% displaychatline chat_object %}
                   '''
        result += loader.get_template_from_string(contents).render(Context({'chat_object': post}))
    result = '''<taconite>
                    <append select="#chat">%s</append>
                </taconite>
             ''' % result
    return HttpResponse(result, mimetype='text/xml')

@login_required
def display_online_users(request, p_id):
    user = request.user
    project = get_object_or_404(Project, id = p_id)
    
    project.check_user_in_project_or_404(user)
    
    chat_data_objects = ChatData.objects.filter(project = project, is_connected = True)
    result = ''
    for user_online in [chat_data.user for chat_data in chat_data_objects]:
        contents = '''{% load usernamegen %}
                      <p><strong>{% usernamegen user "fullname" %}</strong></p>
                   '''
        result += loader.get_template_from_string(contents).render(Context({'user': user_online}))
    result = '''<taconite>
                    <replaceContent select="#users_online">%s</replaceContent>
                </taconite>
             ''' % result
    return HttpResponse(result, mimetype='text/xml')

@login_required
def disconnect(request, p_id):
    user = request.user
    project = get_object_or_404(Project, id = p_id)
    
    project.check_user_in_project_or_404(user)
    
    try:
        chat_data = ChatData.objects.get(project = project, user = user)
    except ChatData.DoesNotExist:
        chat_data = ChatData(user = user, project = project, last_request = -1)
        chat_data.save()
    chat_data.is_connected = False;
    chat_data.save()
    return HttpResponse('')


@login_required
def logs(request, p_id):
    user = request.user
    project = get_object_or_404(Project, id = p_id)
    
    form = LogForm()
    
    from_date = None
    to_date = None
    if request.method == 'GET':
        form = LogForm(request.GET)
        if form.is_valid():
            from_date = form.cleaned_data.get('from_date')
            to_date = form.cleaned_data.get('to_date')
    posts = Post.objects.filter(project = project)
    if from_date:
        posts = posts.exclude(date__lt = from_date)
    if to_date:
        # 1 day is added to the upper date because it also compares the
        # time and the time is the minimum as only the date was set.
        posts = posts.exclude(date__gt = to_date + timedelta(1))
    context = {'project': project, 'form': form, 'logs': posts}
    return render_to_response("chat/logs.html", context, 
                              context_instance = RequestContext(request))