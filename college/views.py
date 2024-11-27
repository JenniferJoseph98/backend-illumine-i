from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Student,Faculty,Subject
from rest_framework.exceptions import NotFound
from .serializers import StudentSerializer,FacultySerializer,SubjectSerializer,CustomSubjectSerializer,LimitedStudentSerializer,FacultyWithSubjectsSerializer
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os

#upload profile picture
class UpdateProfilePicView(APIView):

    def put(self, request, studentId):
        try:
            student = Student.objects.get(studentId=studentId)
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        profile_pic = request.FILES.get('profile_pic')
        if not profile_pic:
            return Response({"error": "No image file provided."}, status=status.HTTP_400_BAD_REQUEST)

        student.profile_pic = profile_pic
        student.save()

        return Response({
            "message": "Profile picture updated successfully.",
            "rl": student.profile_pic.url
        }, status=status.HTTP_200_OK)
        
        


def index(request):
    return HttpResponse('Hello World, Have a Good day')

#Add student
class AddStudentView(APIView):
    def post(self, request,facultyId):
        try:
            if not facultyId:
                return Response(
                    {"status": "error", "message": "facultyId is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            faculty = Faculty.objects.get(facultyId=facultyId)  
            
            serializer = StudentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()  # Save the student record
                return Response(
                    {"status": "success", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"status": "error", "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Faculty.DoesNotExist:
            return Response(
                {"status": "error", "message": "Invalid facultyId. Faculty not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    
# Faculty Login
class FacultyLoginAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        code = request.data.get('code')

        if code != "1234":
            return Response({"error": "Invalid Employee Code"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            faculty = Faculty.objects.get(email=email)
            exists = Subject.objects.filter(faculty=faculty.id).exists()
            
            expected_password = f"{email[:4]}{faculty.contact_number[-4:]}"  # first 4 of email and last 4 of contact
            print(expected_password)
            if password == expected_password:
                return Response({"message": "Login Successful", "faculty_id": faculty.facultyId,"subject":exists,"name":faculty.name}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid Password"}, status=status.HTTP_401_UNAUTHORIZED)
        except Faculty.DoesNotExist:
            return Response({"error": "Faculty Not Found"}, status=status.HTTP_404_NOT_FOUND)


#Student Login

class StudentLoginAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
     

        try:
            student = Student.objects.get(email=email)
            expected_password = f"{email[:4]}{student.contact_number[-4:]}"  # First 4 letters of name, last 4 of contact
            if password == expected_password:
                return Response({"message": "Login Successful", "student_id": student.studentId, "name":student.first_name}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid Password"}, status=status.HTTP_401_UNAUTHORIZED)
        except Student.DoesNotExist:
            return Response({"error": "Student Not Found"}, status=status.HTTP_404_NOT_FOUND)

  
  
  
        

# View all students (GET)
class ViewStudentView(APIView):
    def get(self, request,skip):
        limit=5
        students = Student.objects.all()[skip:skip + limit]  # Query all students
        serializer = StudentSerializer(students, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)



# View all Faculty (GET)
class ViewFacultyView(APIView):
    def get(self, request,skip):
        limit=5
        faculty = Faculty.objects.all()[skip:skip + limit]  # Query all students
        serializer = FacultyWithSubjectsSerializer(faculty, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
    

#View Student details by id
class ViewStudentById(APIView):
    def get(self, request, student_id=None):
        try:
            student = Student.objects.get(studentId=student_id)
        except Student.DoesNotExist:
            raise NotFound(detail="Student not found.")
        serializer = StudentSerializer(student)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

#View Faculty details by id
class ViewFacultyById(APIView):
    def get(self, request, facultyId=None):
        try:
            faculty = Faculty.objects.get(facultyId=facultyId)
        except Faculty.DoesNotExist:
            raise NotFound(detail="Faculty not found.")
        serializer = FacultySerializer(faculty)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
      
  
#Update student  
class UpdateStudentView(APIView):
    def put(self, request):
        try:
            faculty_id = request.data.get("facultyId")
            student_id = request.data.get("studentId")
            if not faculty_id and not student_id:
                return Response(
                    {"status": "error", "message": "facultyId or studentId is required to update a student record."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if faculty_id:
                try:
                    Faculty.objects.get(facultyId=faculty_id)
                    student = Student.objects.get(studentId=student_id)
                except Faculty.DoesNotExist:
                    return Response(
                        {"status": "error", "message": "Invalid facultyId. Faculty not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                except Student.DoesNotExist:
                    return Response(
                        {"status": "error", "message": "Invalid updateStudentId. Student not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif student_id:
                try:
                    student = Student.objects.get(studentId=student_id)
                    print(student.studentId , student_id)
                    
                    if str(student.studentId) != str(student_id):
                        return Response(
                            {"status": "error", "message": "Students can only update their own data."},
                            status=status.HTTP_403_FORBIDDEN
                        )
                except Student.DoesNotExist:
                    return Response(
                        {"status": "error", "message": "Invalid studentId. Student not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )

            serializer = StudentSerializer(student, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": "success", "message": "Student record updated successfully.", "data": serializer.data},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": "error", "message": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

# Add Subject

class AddSubjectView(APIView):
    def post(self, request):
        try:
            faculty_id = request.data.get("facultyId")
            subject_name = request.data.get("name")
            
            if not faculty_id:
                return Response(
                    {"status": "error", "message": "facultyId is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not subject_name:
                return Response(
                    {"status": "error", "message": "Subject name is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                faculty = Faculty.objects.get(facultyId=faculty_id)
            except Faculty.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Invalid facultyId. Faculty not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if Subject.objects.filter(faculty=faculty).exists():
                return Response(
                    {"status": "error", "message": "This faculty already has a subject assigned."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subject = Subject.objects.create(name=subject_name, faculty=faculty)

            serializer = SubjectSerializer(subject)
            return Response(
                {"status": "success", "message": "Subject created successfully.", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



#View Subject details for one faculty with the help of FacultyId
            
class SubjectByFacultyView(APIView):
    def get(self, request, faculty_id):
        try:
            
            subjects = Subject.objects.select_related('faculty').prefetch_related('students').filter(faculty__facultyId=faculty_id)
            
            serializer = CustomSubjectSerializer(subjects, many=True)
            
            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

         
#Student enrollment

class EnrollStudentView(APIView):
    def post(self, request):
        try:
            subject_id = request.data.get("subjectId")
            student_id = request.data.get("studentId")

            if not subject_id:
                return Response(
                    {"status": "error", "message": "SubjectId is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not student_id:
                return Response(
                    {"status": "error", "message": "StudentId is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                subject = Subject.objects.get(subjectId=subject_id)
            except Subject.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Invalid SubjectId. Subject not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                student = Student.objects.get(studentId=student_id)
            except Student.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Invalid StudentId. Student not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if subject.students.filter(studentId=student_id).exists():
                return Response(
                    {"status": "error", "message": "Student is already enrolled in this subject."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subject.students.add(student)
            return Response(
                {"status": "success", "message": "Student enrolled successfully in the subject."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





#Enrolled course


class EnrolledSubjectsView(APIView):
    def get(self, request,student_id):
        try:
            if not student_id:
                return Response(
                    {"status": "error", "message": "StudentId is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                student = Student.objects.get(studentId=student_id)
            except Student.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Invalid StudentId. Student not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            subjects = Subject.objects.filter(students=student)
            serializer = SubjectSerializer(subjects, many=True)

            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
          
#Available course

class AvailableCoursesView(APIView):
    def get(self, request,student_id):
        try:            
            if not student_id:
                return Response(
                    {"status": "error", "message": "StudentId is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                student = Student.objects.get(studentId=student_id)
            except Student.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Invalid StudentId. Student not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            subjects = Subject.objects.exclude(students=student)
            serializer = SubjectSerializer(subjects, many=True)

            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )          
            
                   
class EnrollStudentInFacultySubject(APIView):
    def post(self, request):
        try:
            faculty_id = request.data.get("facultyId")
            student_id = request.data.get("studentId")

            if not faculty_id or not student_id:
                return Response(
                    {"status": "error", "message": "facultyId and studentId are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                faculty = Faculty.objects.get(facultyId=faculty_id)
            except Faculty.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Invalid facultyId. Faculty not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                student = Student.objects.get(studentId=student_id)
            except Student.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Invalid studentId. Student not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                subject = Subject.objects.get(faculty=faculty)
            except Subject.DoesNotExist:
                return Response(
                    {"status": "error", "message": "No subject found for this faculty."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if subject.students.filter(studentId=student_id).exists():
                return Response(
                    {"status": "error", "message": "Student is already enrolled in this subject."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subject.students.add(student)
            return Response(
                {"status": "success", "message": "Student successfully enrolled in the subject."},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Get Students Not Enrolled in Faculty's Subject
class UnenrolledStudent(APIView):
    def get(self, request, faculty_id):
        try:
            try:
                faculty = Faculty.objects.get(facultyId=faculty_id)
            except Faculty.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Invalid facultyId. Faculty not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                subject = Subject.objects.get(faculty=faculty)
            except Subject.DoesNotExist:
                return Response(
                    {"status": "error", "message": "No subject found for this faculty."},
                    status=status.HTTP_404_NOT_FOUND
                )

            students_not_enrolled = Student.objects.exclude(subjects=subject)

            student_data = LimitedStudentSerializer(students_not_enrolled, many=True)

            return Response(
                {"status": "success", "data": student_data.data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
