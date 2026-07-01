from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):

    queryset = Product.objects.all().order_by("-id")

    serializer_class = ProductSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(
            user=self.request.user
        ).order_by("-id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)