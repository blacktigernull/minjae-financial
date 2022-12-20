def check_required_params(params, required_props):
  prop_list = []
  for prop in required_props:
    if prop in params:
      prop_list.append(params[prop])
    else:
      return None, f"{prop} is required"
  return prop_list, None