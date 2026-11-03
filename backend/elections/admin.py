from django.contrib import admin
from .models import Election, Candidate, Ballot


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'starts_at', 'ends_at', 'is_active',
                    'max_choices', 'results_public']
    list_filter = ['is_active', 'results_public']
    inlines = [CandidateInline]


@admin.register(Ballot)
class BallotAdmin(admin.ModelAdmin):
    list_display = ['election', 'voter', 'submitted_at']
    list_filter = ['election']
