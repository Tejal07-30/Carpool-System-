from django.db import models
class Node(models.Model):
    name=models.CharField(max_length=100,unique=True)
    description=models.TextField(blank=True)
    def __str__(self):
        return self.name
class Edge(models.Model):
    fromnode=models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name="outgoingedges"
    )
    tonode=models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name="incomingedges"
    )
    def __str__(self):
        return f"{self.fromnode} -> {self.tonode}"
    class Meta:
        unique_together=("fromnode","tonode")