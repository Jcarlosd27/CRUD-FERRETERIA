import re

def format_chilean_phone_number(user_input):
    """
    Formatea un número de teléfono chileno.

    Args:
    user_input (str): El número de teléfono ingresado por el usuario.

    Returns:
    str: El número formateado o un mensaje de error.
    """
    # Eliminar todos los caracteres que no son dígitos
    digits = re.sub(r'\D', '', user_input)

    # Validar que el número tenga exactamente 9 dígitos
    if len(digits) != 9:
        return "Número inválido. Debe tener exactamente 9 dígitos."

    # Validar que el número comience con '9'
    if not digits.startswith('9'):
        return "Número inválido. Debe comenzar con '9'."

    # Formatear el número en el formato deseado: +56 9 xxxx xxxx
    formatted_number = f"+56 9 {digits[1:5]} {digits[5:]}"
    return formatted_number

def format_chilean_telephone_number(user_input):
    """
    Formatea un número de teléfono fijo chileno.

    Args:
    user_input (str): El número de teléfono fijo ingresado por el usuario.

    Returns:
    str: El número formateado o un mensaje de error.
    """
    # Eliminar todos los caracteres que no son dígitos
    digits = re.sub(r'\D', '', user_input)

    # Validar que el número tenga 7 u 8 dígitos
    if len(digits) == 7:
        # Formatear el número en el formato deseado: +56 2 xxxx xxx
        formatted_number = f"+56 2 {digits[:4]} {digits[4:]}"
        return formatted_number

    elif len(digits) == 8:
        # Formatear el número en el formato deseado: +56 3 xxxx xxxx (código de área)
        area_code = digits[:2]  # Los dos primeros dígitos como código de área
        formatted_number = f"+56 {area_code} {digits[2:6]} {digits[6:]}"
        return formatted_number

    return "Número inválido. Debe tener 7 o 8 dígitos."