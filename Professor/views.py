from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
import UserAuth.utils as UserAuthutils
from django.conf import settings
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import *
from Doubt.models import *
from Meeting.models import Meeting
import hashlib
import time

group_name = 'Professor'
login_url = 'UserAuth:login'

def group_required(*group_names, login_url=None):
    def in_groups(u):
        if u.is_authenticated:
            if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
                return True
        return False
    return user_passes_test(in_groups, login_url=login_url)

@login_required(login_url=login_url)
@group_required(group_name, login_url=login_url)
def dashboard(request):
    if request.method == 'GET':
        # if UserAuthutils.is_user_verfied(request):
        #     poll_list = Poll.objects.filter(professor__user__user__username=request.user.username)
        #     return render(request, 'Professor/dashboard.html', {"poll_list": poll_list})
        # else:
        #     # return render(request, 'Professor/verify_account.html')
        #     return render(request, 'Professor/dashboard.html')
        poll_list = Poll.objects.filter(professor__user__user__username=request.user.username)
        quiz_list = Quiz.objects.filter(professor__user__user__username=request.user.username)
        course_list = CourseProfessor.objects.filter(professor__user__user__id=request.user.id)
        # doubt_list = Doubts.objects.filter(course=)
        meeting_list = Meeting.objects.filter(professor__user__user__id=request.user.id)
        active_poll_list = ConductPoll.objects.filter(poll__professor__user__user__username=request.user.username, active=True)
        active_quiz_list = ConductQuiz.objects.filter(quiz__professor__user__user__username=request.user.username, active=True)
        # print(poll_list)
        return render(request, 'Professor/dashboard.html', {"poll_list": poll_list, "quiz_list": quiz_list, "course_list":course_list, "meeting_list":meeting_list, "active_quiz_list": active_quiz_list, "active_poll_list": active_poll_list})

@login_required(login_url=login_url)
@group_required(group_name, login_url=login_url)
def create_poll(request):
    if request.method == 'GET':
        course_list = CourseProfessor.objects.filter(professor__user__user__username=request.user.username)
        return render(request, 'Professor/create-poll.html', {'course_list': course_list})

    if request.method == 'POST':
        course = request.POST.get('course')
        title = request.POST.get('title')
        question = request.POST.get('question')
        option_list = request.POST.getlist('poll_options[]')

        print(option_list)

        try:
            poll_inst = Poll()
            poll_inst.professor = ProfessorProfile.objects.get(user__user__username=request.user.username)
            poll_inst.course = Course.objects.get(id=course)
            poll_inst.title = title
            poll_inst.question = question
            poll_inst.save()

            for option in option_list:
                option_inst = PollOption()
                option_inst.poll = poll_inst
                option_inst.option = option
                option_inst.save()
            return HttpResponseRedirect(reverse('Professor:dashboard'))
        except Exception as e:
            print(e)

@login_required(login_url=login_url)
@group_required(group_name, login_url=login_url)
def show_poll(request, poll_id):
    if request.method == 'GET':
        poll_details = Poll.objects.get(id=poll_id)
        poll_options = PollOption.objects.filter(poll__id=poll_id)
        is_poll_active = ConductPoll.objects.filter(active=True, poll__id=poll_id)
        return render(request, 'Professor/poll-detail.html', {"poll_details": poll_details, 'poll_options': poll_options, "is_poll_active": is_poll_active})

@login_required(login_url=login_url)
@group_required(group_name, login_url=login_url)
def create_quiz(request):
    if request.method == 'GET':
        course_list = CourseProfessor.objects.filter(professor__user__user__username=request.user.username)
        return render(request, 'Professor/create-quiz.html', {'course_list': course_list})

    if request.method == 'POST':
        try:
            print(request.POST)
            # print(request.POST['course'])
            question_option_array = list(map(int, request.POST['question-option'].split(',')))
            # print(question_option_array)

            quiz = Quiz()
            quiz.professor = ProfessorProfile.objects.get(user__user__username=request.user.username)
            course = CourseProfessor.objects.get(id=int(request.POST['course']))
            # print(course.course.id)
            quiz.course = Course.objects.get(id=int(course.course.id))
            quiz.title = request.POST['title']
            quiz.description = request.POST['description']
            quiz.max_marks = request.POST['max_marks']
            quiz.pass_marks = request.POST['pass_marks']
            # quiz.unique_quiz_id = Course.objects.get(id=int(request.POST['course'])).code + '_' + request.POST['title'] + '_' + str(hashlib.sha224(((request.POST['title'])).encode('utf-8')).hexdigest())[:5]
            quiz.save()

            for i in range(len(question_option_array)):
                # print('question ', i+1)
                if question_option_array[i] != 0:
                    ques_inst = QuizQuestion()
                    ques_inst.quiz = quiz
                    ques_inst.question = request.POST['question_'+str(i+1)]
                    ques_inst.marks = request.POST['marks_'+str(i+1)]
                    ques_inst.time = request.POST['time_'+str(i+1)]
                    ques_inst.save()

                    option_list = request.POST.getlist('poll_options_'+str(i+1)+'[]')
                    # print(option_list)
                    for j in range(len(option_list)):
                        # print(option_list[j])
                        opt_inst = QuizOptions()
                        opt_inst.quiz = quiz
                        opt_inst.question = ques_inst
                        opt_inst.option = option_list[j]
                        if request.POST.get('option_checkbox_'+str(i+1)+'_'+str(j+1)) is not None:
                            opt_inst.is_correct = True
                        else:
                            opt_inst.is_correct = False
                        opt_inst.save()
            messages.success(request, "Successfully Created Quiz")
            return HttpResponseRedirect(reverse('Professor:dashboard'))
        except Exception as e:
            print('error is ', e)
            messages.warning(request, "There was an error creating Quiz. Please Try Again.")
            return HttpResponseRedirect(reverse('Professor:create-quiz'))

@login_required(login_url=login_url)
@group_required(group_name, login_url=login_url)
def show_quiz(request, quiz_id):
    if request.method == 'GET':
        quiz_data = QuizOptions.objects.filter(quiz__id=quiz_id)
        is_quiz_active = ConductQuiz.objects.filter(active=True, quiz__id=quiz_id)
        return render(request, 'Professor/quiz-detail.html', {"quiz_data": quiz_data, "is_quiz_active": is_quiz_active})

@login_required(login_url=login_url)
@group_required(group_name, login_url=login_url)
def conduct_quiz(request, quiz_id):
    if request.method == 'GET':
        try:
            quiz = Quiz.objects.get(id=quiz_id)
            unique_quiz_id = str('_'.join(quiz.title.split(' ')))+str(hashlib.sha224((str(quiz.title)+str(time.strftime("%Y-%m-%d"))+str(time.strftime("%H:%i:%s"))+str(quiz.id)).encode('utf-8')).hexdigest())[:5]

            conduct_quiz_inst = ConductQuiz()
            conduct_quiz_inst.quiz = quiz
            conduct_quiz_inst.unique_quiz_id = unique_quiz_id
            conduct_quiz_inst.active = True
            conduct_quiz_inst.save()

            messages.success(request, "Successfully started quiz")
            return HttpResponseRedirect(reverse('Professor:quiz', kwargs={'quiz_id':quiz_id}))
        except Exception as e:
            print(e)
            messages.warning(request, "There was an error conducting Quiz. Please Try Again.")
            return HttpResponseRedirect(reverse('Professor:quiz', kwargs={'quiz_id':quiz_id}))

@login_required(login_url=login_url)
@group_required(group_name, login_url=login_url)
def stop_quiz(request, quiz_id):
    if request.method == 'GET':
        try:
            conduct_quiz_inst = ConductQuiz.objects.get(id=quiz_id)
            conduct_quiz_inst.active = False
            conduct_quiz_inst.save()
            messages.success(request, "Successfully stopped quiz")
            return HttpResponseRedirect(reverse('Professor:quiz', kwargs={'quiz_id':conduct_quiz_inst.quiz.id}))
        except Exception as e:
            print(e)
            messages.warning(request, "There was an error stopping Quiz. Please Try Again.")
            return HttpResponseRedirect(reverse('Professor:quiz', kwargs={'quiz_id':conduct_quiz_inst.quiz.id}))

@login_required(login_url=login_url)
@group_required(group_name, login_url=login_url)
def conduct_poll(request, poll_id):
    if request.method == 'GET':
        try:
            poll = Poll.objects.get(id=poll_id)
            unique_poll_id = str('_'.join(poll.title.split(' ')))+str(hashlib.sha224((str(poll.title)+str(time.strftime("%Y-%m-%d"))+str(time.strftime("%H:%i:%s"))+str(poll.id)).encode('utf-8')).hexdigest())[:5]

            conduct_poll_inst = ConductPoll()
            conduct_poll_inst.poll = poll
            conduct_poll_inst.unique_poll_id = unique_poll_id
            conduct_poll_inst.active = True
            conduct_poll_inst.save()

            messages.success(request, "Successfully started Poll")
            return HttpResponseRedirect(reverse('Professor:poll', kwargs={'poll_id':poll_id}))
        except Exception as e:
            print(e)
            messages.warning(request, "There was an error conducting Poll. Please Try Again.")
            return HttpResponseRedirect(reverse('Professor:poll', kwargs={'poll_id':poll_id}))

@login_required(login_url=login_url)
@group_required(group_name, login_url=login_url)
def stop_poll(request, poll_id):
    if request.method == 'GET':
        try:
            conduct_poll_inst = ConductPoll.objects.get(id=poll_id)
            conduct_poll_inst.active = False
            conduct_poll_inst.save()
            messages.success(request, "Successfully stopped Poll")
            return HttpResponseRedirect(reverse('Professor:poll', kwargs={'poll_id':conduct_poll_inst.poll.id}))
        except Exception as e:
            print(e)
            messages.warning(request, "There was an error stopping Poll. Please Try Again.")
            return HttpResponseRedirect(reverse('Professor:poll', kwargs={'poll_id':conduct_poll_inst.poll.id}))