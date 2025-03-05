# Leave Management System (Django + React)

# Backend (Django, Python)
from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import jwt
from django.conf import settings
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate

# Database Models
class Department(models.Model):
    name = models.CharField(max_length=100)
    head = models.ForeignKey(User, on_delete=models.CASCADE, related_name='department_head')

class LeaveRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default='Pending')

# API Views
@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = authenticate(username=data['username'], password=data['password'])
        if user:
            token = jwt.encode({'user_id': user.id, 'role': user.is_superuser}, settings.SECRET_KEY, algorithm='HS256')
            return JsonResponse({'message': 'Login successful', 'token': token, 'user_id': user.id, 'role': user.is_superuser})
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

@csrf_exempt
def apply_leave(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = get_object_or_404(User, id=data['user_id'])
        LeaveRequest.objects.create(
            user=user,
            leave_type=data['leave_type'],
            start_date=data['start_date'],
            end_date=data['end_date']
        )
        return JsonResponse({'message': 'Leave request submitted'})

@csrf_exempt
def approve_leave(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        leave_request = get_object_or_404(LeaveRequest, id=data['leave_id'])
        leave_request.status = data['status']
        leave_request.save()
        return JsonResponse({'message': 'Leave status updated'})

# URL Configuration (urls.py)
from django.urls import path
urlpatterns = [
    path('login/', login),
    path('apply-leave/', apply_leave),
    path('approve-leave/', approve_leave),
]

# Frontend (React, JavaScript)
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './styles.css';

function AdminPanel() {
    const [leaveRequests, setLeaveRequests] = useState([]);
    
    useEffect(() => {
        axios.get('http://localhost:8000/leave-requests/').then(response => {
            setLeaveRequests(response.data);
        });
    }, []);
    
    const approveLeave = (leaveId) => {
        axios.post('http://localhost:8000/approve-leave/', { leave_id: leaveId, status: 'Approved' })
            .then(() => {
                setLeaveRequests(prev => prev.map(req => req.id === leaveId ? { ...req, status: 'Approved' } : req));
            });
    };
    
    return (
        <div className="admin-panel">
            <h2>Admin Panel</h2>
            {leaveRequests.map(request => (
                <div key={request.id} className="leave-card">
                    <p>{request.user}: {request.leave_type} ({request.start_date} - {request.end_date}) - {request.status}</p>
                    {request.status === 'Pending' && <button onClick={() => approveLeave(request.id)}>Approve</button>}
                </div>
            ))}
        </div>
    );
}

function LeaveManagement() {
    const [leaveType, setLeaveType] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [message, setMessage] = useState('');

    const applyLeave = async () => {
        try {
            const response = await axios.post('http://localhost:8000/apply-leave/', {
                user_id: 1, // Replace with actual user id
                leave_type: leaveType,
                start_date: startDate,
                end_date: endDate
            });
            setMessage(response.data.message);
        } catch (error) {
            setMessage('Error applying for leave');
        }
    };

    return (
        <div className="leave-management">
            <h2>Apply for Leave</h2>
            <input type="text" placeholder="Leave Type" value={leaveType} onChange={(e) => setLeaveType(e.target.value)} />
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            <button onClick={applyLeave}>Submit</button>
            {message && <p>{message}</p>}
        </div>
    );
}

export { LeaveManagement, AdminPanel };

/* styles.css */
.admin-panel, .leave-management {
    background-color: white;
    color: black;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    max-width: 600px;
    margin: auto;
}

body {
    background-color: #007bff;
    font-family: Arial, sans-serif;
    text-align: center;
}

button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 5px;
    cursor: pointer;
    margin-top: 10px;
}

button:hover {
    background-color: #0056b3;
}