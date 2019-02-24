# the following try/except block will make the custom check compatible with any Agent version
try:
  # first, try to import the base class from old versions of the Agent...
  from checks import AgentCheck
except ImportError:
  # ...if the above failed, the check is running in Agent version 6 or later
  from datadog_checks.checks import AgentCheck
  
from datadog_checks.utils.subprocess_output import get_subprocess_output
import json
import sys

# content of the special variable __version__ will be shown in the Agent status page
__version__ = "1.0.0"

class CustomLighthouse(AgentCheck):
  def check(self, instance):
    cmd = ["/usr/local/bin/lighthouse", instance["url"], "--output", "json", "--quiet", "--chrome-flags='--headless'"]

    json_string, error_message, exit_code = get_subprocess_output(cmd, self.log, raise_on_empty_output=False)
    
    # check for error since we have raise_on_empty_output set to False
    if exit_code > 0:
      raise Exception(json_string, error_message, exit_code)

    try:
      data = json.loads(json_string)
      score_accessibility = data["categories"]["accessibility"]["score"] * 100
      score_best_practices = data["categories"]["best-practices"]["score"] * 100
      score_performance = data["categories"]["performance"]["score"] * 100
      score_pwa = data["categories"]["pwa"]["score"] * 100
      score_seo = data["categories"]["seo"]["score"] * 100
    except Exception:
      self.log.warn("lighthouse response JSON structure different than expected")
      raise Exception(json_string, error_message, exit_code)

    # add tags
    try:
      tags = instance['tags']
      if type(tags) != list:
        self.log.warn('The tags list in the lighthouse check is not configured properly')
        tags = []
    except KeyError:
      tags = []

    tags.append("lighthouse_url:%s" % instance['url'])
    tags.append("lighthouse_name:%s" % instance['name'])

    self.gauge("custom_lighthouse.accessibility", score_accessibility, tags=tags)
    self.gauge("custom_lighthouse.best_practices", score_best_practices, tags=tags)
    self.gauge("custom_lighthouse.performance", score_performance, tags=tags)
    self.gauge("custom_lighthouse.pwa", score_pwa, tags=tags)
    self.gauge("custom_lighthouse.seo", score_seo, tags=tags)