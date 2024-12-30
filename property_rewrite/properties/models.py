from django.db import models

class Property(models.Model):
    original_id = models.BigIntegerField(default=0)  # Default for existing rows
    original_title = models.TextField(default="Unknown")  # Default for existing rows
    rewritten_title = models.TextField(default="Not rewritten")  # Default for existing rows
    description = models.TextField(default="Not rewritten")  # New field for the description
    class Meta:
        db_table = 'rewrite_property_info'

    def __str__(self):
        return f"{self.original_title} -> {self.rewritten_title}"
