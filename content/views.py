import logging
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.db.models import Sum, Prefetch, Count, Q

from .models import News, CompanyInfo, CompanyHistory, FAQ, Review
from content.models import Vacancy, PromoCode
from cleaning.models import ServiceType, Service, Order, OrderItem
from users.models import Employee
from .forms import ReviewForm
from .services import get_categorized_promo_codes

logger = logging.getLogger(__name__)

class PublicHomeView(TemplateView):
    template_name = 'content/public_home.html'

    def get_context_data(self, **kwargs):
        logger.info("Public home page accessed")
        context = super().get_context_data(**kwargs)
        context['latest_news'] = News.objects.order_by('-pub_date').first()
        return context

class AboutCompanyView(TemplateView):
    template_name = 'content/about_company.html'

    def get_context_data(self, **kwargs):
        logger.info("About company page accessed")
        context = super().get_context_data(**kwargs)
        context['company'] = CompanyInfo.objects.first()
        context['history'] = CompanyHistory.objects.all().order_by('year')
        return context

class NewsListView(ListView):
    model = News
    template_name = 'content/news_list.html'
    context_object_name = 'news_list'
    ordering = ['-pub_date']

    def get_queryset(self):
        logger.info("Fetching news list")
        return super().get_queryset()

class NewsDetailView(DetailView):
    model = News
    template_name = 'content/news_detail.html'
    context_object_name = 'article'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        logger.info(f"News article accessed: {obj.title}")
        return obj

class FAQListView(ListView):
    model = FAQ
    template_name = 'content/faq_list.html'
    context_object_name = 'faqs'
    ordering = ['-date_added']

    def get_queryset(self):
        logger.info("Fetching FAQ list")
        return super().get_queryset()

class PrivacyPolicyView(TemplateView):
    template_name = 'content/privacy_policy.html'

    def get(self, request, *args, **kwargs):
        logger.info("Privacy policy page accessed")
        return super().get(request, *args, **kwargs)

class VacancyListView(ListView):
    model = Vacancy
    template_name = 'content/vacancy_list.html'
    context_object_name = 'vacancies'

    def get_queryset(self):
        logger.info("Fetching active vacancies")
        return Vacancy.objects.filter(is_active=True)

class ReviewListView(ListView):
    model = Review
    template_name = 'content/reviews.html'
    context_object_name = 'reviews'
    ordering = ['-date']

    def get_context_data(self, **kwargs):
        logger.info("Reviews page accessed")
        context = super().get_context_data(**kwargs)
        context['form'] = ReviewForm()
        context['is_client'] = self.request.user.is_authenticated and hasattr(self.request.user, 'client_profile')
        return context

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'client_profile'):
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.client = request.user.client_profile
                review.save()
                logger.info(f"New review submitted by client: {request.user.username}")
            else:
                logger.warning(f"Invalid review form submission by: {request.user.username}")
        return redirect('content:review_list')

class PromoCodeListView(TemplateView):
    template_name = 'content/promo_list.html'

    def get_context_data(self, **kwargs):
        logger.info("Promo codes list accessed")
        context = super().get_context_data(**kwargs)
        context.update(get_categorized_promo_codes())
        return context

class CatalogListView(ListView):
    model = ServiceType
    template_name = 'content/catalog.html'
    context_object_name = 'categories'

    def get_queryset(self):
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        logger.info(f"Catalog accessed with filters - min_price: {min_price}, max_price: {max_price}")

        queryset = ServiceType.objects.all()
        service_qs = Service.objects.all()

        if min_price and min_price.isdigit():
            service_qs = service_qs.filter(price__gte=min_price)
        if max_price and max_price.isdigit():
            service_qs = service_qs.filter(price__lte=max_price)

        return queryset.prefetch_related(Prefetch('services', queryset=service_qs))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_client'] = user.is_authenticated and hasattr(user, 'client_profile')

        popular = Service.objects.annotate(total_sold=Sum('orderitem__quantity')).order_by('-total_sold').first()
        context['popular_service'] = popular

        top_services = Service.objects.annotate(total_sold=Sum('orderitem__quantity')).exclude(total_sold=None).order_by('-total_sold')[:5]
        context['chart_labels'] = json.dumps([s.name for s in top_services])
        context['chart_values'] = json.dumps([s.total_sold for s in top_services])

        return context

class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, 'client_profile'):
            logger.warning(f"Non-client user {request.user.username} tried to add item to cart")
            messages.error(request, "Only registered clients can add items to the cart.")
            return redirect('content:catalog')

        service_id = request.POST.get('service_id')
        service = get_object_or_404(Service, id=service_id)

        if 'cart' not in request.session:
            request.session['cart'] = {}

        cart = request.session['cart']
        cart[str(service_id)] = cart.get(str(service_id), 0) + 1
        request.session.modified = True

        logger.info(f"Service '{service.name}' added to cart by {request.user.username}")
        messages.success(request, f"'{service.name}' was added to your cart.")
        return redirect('content:catalog')

class CartView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, 'client_profile'):
            logger.warning(f"Unauthorized cart access attempt by {request.user.username}")
            messages.error(request, "Only clients can access the cart.")
            return redirect('content:catalog')

        logger.info(f"Client {request.user.username} accessing cart")
        cart = request.session.get('cart', {})
        cart_items = []
        total_cost = 0

        for service_id, quantity in cart.items():
            try:
                service = Service.objects.get(id=service_id)
                cost = service.price * quantity
                total_cost += cost
                cart_items.append({'service': service, 'quantity': quantity, 'cost': cost})
            except Service.DoesNotExist:
                logger.error(f"Service ID {service_id} in cart session does not exist")
                continue

        new_orders = Order.objects.filter(client=request.user.client_profile, status=Order.Status.NEW).order_by('-date_created')

        return render(request, 'content/cart.html', {
            'cart_items': cart_items,
            'total_cost': total_cost,
            'new_orders': new_orders
        })

    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not cart:
            logger.warning(f"Order attempt with empty cart by {request.user.username}")
            messages.error(request, "Your cart is empty.")
            return redirect('content:catalog')

        address = request.POST.get('address')
        date_execution = request.POST.get('date_execution')
        promo_code_str = request.POST.get('promo_code', '').strip()
        action = request.POST.get('action')

        logger.info(f"Processing checkout for {request.user.username}. Address: {address}, Action: {action}")

        required_service_type_ids = set()
        services_to_order = []

        for service_id, quantity in cart.items():
            try:
                service = Service.objects.get(id=service_id)
                services_to_order.append({'service': service, 'quantity': quantity})
                required_service_type_ids.add(service.service_type.id)
            except Service.DoesNotExist:
                continue

        suitable_employees = Employee.objects.annotate(
            covered_types_count=Count(
                'specializations__service_types',
                filter=Q(specializations__service_types__id__in=required_service_type_ids),
                distinct=True
            )
        ).filter(covered_types_count=len(required_service_type_ids))

        if not suitable_employees.exists():
            logger.error(f"No suitable employee found for service types: {list(required_service_type_ids)}")
            messages.error(request, "Order cannot be created. No single employee has enough specializations.")
            return redirect('content:cart')

        best_employee = suitable_employees.annotate(current_orders=Count('orders')).order_by('current_orders').first()
        logger.info(f"Employee {best_employee.user.username} selected for order")

        promo_code = None
        if promo_code_str:
            try:
                promo_code = PromoCode.objects.get(code=promo_code_str, is_archived=False)
                logger.info(f"Promo code applied: {promo_code_str}")
            except PromoCode.DoesNotExist:
                logger.warning(f"Invalid promo code attempt: {promo_code_str}")
                messages.error(request, "Invalid or expired promo code.")
                return redirect('content:cart')

        order_status = Order.Status.PAID if action == 'pay_now' else Order.Status.NEW
        order = Order.objects.create(
            client=request.user.client_profile,
            employee=best_employee,
            address=address,
            date_execution=date_execution,
            promo_code=promo_code,
            status=order_status
        )

        for item in services_to_order:
            OrderItem.objects.create(order=order, service=item['service'], quantity=item['quantity'], price=item['service'].price)

        request.session['cart'] = {}
        request.session.modified = True

        logger.info(f"Order #{order.id} successfully created for client {request.user.username}")
        return redirect('users:profile')

class RemoveFromCartView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        service_id = str(request.POST.get('service_id'))
        cart = request.session.get('cart', {})

        if service_id in cart:
            del cart[service_id]
            request.session['cart'] = cart
            request.session.modified = True
            logger.info(f"Service ID {service_id} removed from cart by {request.user.username}")
            messages.success(request, "Item removed from cart.")

        return redirect('content:cart')