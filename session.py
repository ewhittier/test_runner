import json
import sanity
import datetime

class Session():
  def __init__(self, ta_obj, hw_obj):
    self.start_time = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M:%S%p")
    self.ta_obj = ta_obj
    self.hw_obj = hw_obj
    self.DATA_DIR = 'data/'
    self.DATA_FILE = 'data.json'
    self.log = {"info":{}, "internal_log":{}, "external_log":{}, "score_key":{}, "score_sum":"", "sanity_compare":{}}
    self._load_data()

  def _arg_compare(self, ta_obj, hw_obj):
    log = []
    ta_funcs = set(sanity.listFunctionNames(ta_obj))
    hw_funcs = set(sanity.listFunctionNames(hw_obj))
    ta_farg = {f:sanity.getFunctionArgCount(ta_obj, f) for f in ta_funcs}
    hw_farg = {f:sanity.getFunctionArgCount(hw_obj, f) for f in hw_funcs}
    args_there = True #innocent until proven guilty

    for func, arg_count in ta_farg.items():
      hw_arg_count = hw_farg[func]
      if arg_count == hw_arg_count:
        log.append("PASSED@{!s}: {!r} args defined in ta-{!s}. {!r} args in submitted-{!s}".format(func, arg_count, ta_obj.__name__ + "." + func, hw_arg_count, hw_obj.__name__ + "." + func))
      else: 
        log.append("ERROR@{!s}: {!r} args defined in ta-{!s}. {!r} args in submitted-{!s}".format(func, arg_count, ta_obj.__name__ + "." + func, hw_arg_count, hw_obj.__name__ + "." + func))
        self.x_log("COMPARE_ERROR", "You defined {!r} args in submitted-{!s}, there should be {!r} argument(s)".format(hw_arg_count, hw_obj.__name__ + "." + func, arg_count))
        args_there = False
    return args_there, log


   '''
   compare() does a basic comparison of two modules (or objects), checking to make sure that all functions and classes
   are defined with the appropriate number of arguments. returns true if so, false otherwise.
   ''' 
  def compare(self, ta_module=None, hw_module=None):
    #if there are no arguments given to compare, use the ta and hw objects associated with the Session
    if ta_module is None:
      ta_module = self.ta_obj

    if hw_module is None:
      hw_module = self.hw_obj

    all_there = True #innocent until proven guilty

    #scrape functions from top level:
    ta_top_lvl = set(sanity.listFunctionNames(ta_module))
    hw_top_lvl = set(sanity.listFunctionNames(hw_module))
    if ta_top_lvl <= hw_top_lvl:
      all_there, log = self._arg_compare(ta_module, hw_module)
      self._clog("top_lvl_funcs", log)
    else:
      #also log the missing ones
      missing = ta_top_lvl - hw_top_lvl
      missing_str = ", ".join(str(e) for e in missing)
      self._clog("top_lvl_funcs", "ERROR: some top level function(s) defined in ta-{!s} are missing in submitted-{!s}: {!s}".format(ta_module.__name__, hw_module.__name__, missing_str))
      self.x_log("COMPARE_ERROR", "You are missing some top level function(s) in {!s}: {!s}".format(hw_module.__name__, missing_str))
      all_there = False

    #scrape classes from TA_file, hw_file, and compare them
    hw_class_dict = sanity.classDict(hw_module)
    ta_class_dict = sanity.classDict(ta_module)
    ta_class_names = set(ta_class_dict.keys())
    hw_class_names = set(hw_class_dict.keys())
    common_class_names = ta_class_names & hw_class_names

    #high level check to make sure all the classes in TA_module are defined in hw_module (no check to see if there's extra stuff defined in hw_module)
    if ta_class_names <= hw_class_names:
      self._clog("classes", "PASSED: all the classes in ta-{!s} exist in {!s}".format(ta_module.__name__, hw_module.__name__))

    else:
      missing = ta_class_names - hw_class_names
      missing_str = ", ".join(str(e) for e in missing)
      self._clog("classes", "ERROR: some classes defined in ta-{!s} are missing from submitted-{!s}: {!s}".format(ta_module.__name__, hw_module.__name__, missing_str))
      self.x_log("COMPARE_ERROR", "You are missing some classes in {!s}: {!s}".format(hw_module.__name__, missing_str))
      all_there = False

    #scrape functions from the common classes:
    for cls_name in common_class_names:
      hw_cls = hw_class_dict[cls_name]
      ta_cls = ta_class_dict[cls_name]
      ta_cls_funcs = set(sanity.listFunctionNames(ta_cls))
      hw_cls_funcs = set(sanity.listFunctionNames(hw_cls))
      cls_func_compare = str(cls_name)+"_funcs"
      if ta_cls_funcs <= hw_cls_funcs:
        cls_args_there, log = self._arg_compare(ta_cls, hw_cls)
        self._clog(cls_func_compare, log)
        if all_there and not cls_args_there:
          all_there = False
      else:
        missing = ta_cls_funcs - hw_cls_funcs
        missing_str = ", ".join(str(e) for e in missing)
        self._clog(cls_func_compare, "ERROR: some functions defined in ta-{!s}'s class {!s} are missing from submitted-{!s}'s class {!s}: {!s}".format(ta_module.__name__, cls_name, hw_module.__name__, cls_name, missing_str))
        self.x_log("COMPARE_ERROR", "Your class {!s} is missing some functions: {!s}".format(hw_module.__name__ +"." + cls_name, missing_str))
        all_there = False

    return all_there



  def _load_data(self):
    submission_data = self.DATA_DIR + self.DATA_FILE
    with open(submission_data) as data_file: 
      self.data = json.load(data_file)

  def _getattempts(self):
    attempts = self.data['attempts']
    return attempts

  def _gettimedelta(self):
    timedelta = self.data['timedelta']
    return timedelta

  def _info(self, key, message):
    self.log["info"][key] = message

  def _clog(self, key, message):
    # if key not in self.log["sanity_compare"]:
    #   self.log["sanity_compare"][key] = []
    # self.log["sanity_compare"][key].append(message) 
    self.log["sanity_compare"][key] = message

  def i_log(self, key, message):
    if key not in self.log["internal_log"]:
      self.log["internal_log"][key] = []
    self.log["internal_log"][key].append(message)

  def x_log(self, key, message):
    if key not in self.log["external_log"]:
      self.log["external_log"][key] = []
    self.log["external_log"][key].append(message)

  def scorekey(self, test, scoreInt):
    self.log["score_key"][test] = scoreInt

  def finalize(self):
    self.log["score_sum"] = sum(self.log["score_key"].values())
    self.end_time = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M:%S%p")
    self._info("start_time", self.start_time)
    self._info("end_time", self.end_time)
    self._info("timedelta", self._gettimedelta())
    self._info("attempts", self._getattempts())

    print(json.dumps(self.log, indent=4))
    return json.dumps(self.log)


# fr = toJSONFormatter()
# logger.logHandler.setFormatter(fr)