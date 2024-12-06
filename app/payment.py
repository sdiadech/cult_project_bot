import stripe

from config.constants import STRIPE_API_KEY

# Stripe API key
stripe.api_key = STRIPE_API_KEY


async def create_payment_intent(amount: float, currency: str = "pln"):
    """
    Create a Stripe PaymentIntent for a given amount.
    """
    payment_intent = stripe.PaymentIntent.create(
        amount=int(amount * 100),  # Stripe expects amounts in cents
        currency=currency,
        payment_method_types=["card"],
    )
    return payment_intent
