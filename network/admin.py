from django.contrib import admin
from .models import Node, Edge
@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    listdisplay=('id','name')

@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    listdisplay=('id', 'from_node', 'to_node')


