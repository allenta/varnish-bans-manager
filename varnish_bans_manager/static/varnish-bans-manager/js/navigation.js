(function ($) {

  vbm.navigation = vbm.navigation || {};

  /**
   *
   */
  function is_enabled() {
    return window.History.enabled;
  }

  /**
   *
   */
  function get_root() {
    var root = (window.location.hostname || window.location.host);
    if (window.location.port || false) {
      root += ':' + window.location.port;
    }
    return root;
  }

  /**
   *
   */
  function is_absolute_url(url) {
    return (url.indexOf('http') === 0);
  }

  /**
   *
   */
  function get_relative_url(url) {
    var root = get_root();
    return url.replace('http://' + root, '').replace('https://' + root, '');
  }

  /**
   *
   */
  function load(data, url) {
    // Get relative URL.
    var relative_url = get_relative_url(url);

    // AJAX request.
    vbm.ajax.call({
      url: url,
      type: 'GET',
      data: data,
      navigation: true,
      before_send: function(xhr, settings) {
        // Close any opened overlays.
        vbm.close_all_overlays();

        // Prepare container.
        $('#content').animate({opacity: 0.2}, 200);

        // Update navigation menu.
        if (vbm.layout == 'authenticated') {
          var home_url = '/' + vbm.language + '/home/';

          // Deactivate everything.
          $('#navbar .nav li').removeClass('active');

          // Active item in primary navbar.
          if (relative_url == home_url) {
            $('#primary-navbar .nav li:first').addClass('active');
          } else {
            $('#primary-navbar ul.nav > li').each(function() {
              if (relative_url.indexOf('/' + vbm.language + $(this).attr('data-path')) === 0) {
                $(this).addClass('active');
              }
            });
          }
        }
      },
      success: function(response, status, xhr) {
        // Restore opacity.
        $('#content').stop(true, true).css('opacity', 1.0).show();
      },
      error: function(xhr, status) {
        if (!xhr.aborted && (status != 'abort') && (status != 'aborted')) {
          // A full reload is the best option to fix the mess.
          window.location = url;
        }
      },
      commands: {
        set_content: function (contents) {
          vbm.commands.set_content(contents);
          vbm.scroll_top();
        }
      }
    });
  }

  /**
   * Adds base36 encoding / decoding to hash for HTML5 non-compliant browsers,
   * to avoid problems with certain characters in the hash.
   */
  History.base_escapeHash = History.escapeHash;
  History.escapeHash = function(hash) {
    var escaped_hash = History.base_escapeHash(hash);
    var result = '';
    for (var i = 0; i < escaped_hash.length; i++) {
      result += escaped_hash.charAt(i).charCodeAt(0).toString(36);
    }
    return result;
  };

  History.base_unescapeHash = History.unescapeHash;
  History.unescapeHash = function(hash) {
    var normalized_hash = History.normalizeHash(hash);
    var escaped_hash = '';
    for (var i = 0; i < normalized_hash.length;) {
      escaped_hash += String.fromCharCode(parseInt('' + normalized_hash.charAt(i++) + normalized_hash.charAt(i++), 36));
    }
    return History.base_unescapeHash(escaped_hash);
  };

  /**
   *
   */
  vbm.navigation.navigate = function(url, options) {
    // Input arguments.
    options = options || {};
    var layout = options.layout || null;
    var submit = options.submit || {};
    // Check AJAX navigation is enabled.
    if (is_enabled()) {
      // Destination URL.
      var relative_url = get_relative_url(url);
      // Previous history state.
      var previous_state = window.History.getState();
      var previous_relative_url = null;
      if (previous_state) {
        previous_relative_url = get_relative_url(previous_state.url);
      }
      // Prepare.
      var data = {
        ajax: true,
        submit: submit,
        serial: (new Date()).getTime() + String(Math.random()).replace(/\D/g,'') + '-' + (vbm.serial++)
      };
      // Push/replace new URL in history.
      if (relative_url == previous_relative_url) {
        window.History.replaceState(data, null, url);
      } else {
        window.History.pushState(data, null, url);
      }
    } else {
      // No AJAX navigation available.
      window.location = url;
    }
  };

  /**
   *
   */
  vbm.navigation.statechange = function() {
    // Prepare some variables.
    var state = window.History.getState();
    var url = state.url;
    var submit = state.data.submit ? state.data.submit : {};

    // Not all URLs in our server can be delivered through AJAX, so we need to
    // check the 'ajax' flag in order to choose between an AJAX or a full request.
    if ((typeof(state.data.ajax) == 'undefined') || (!state.data.ajax)) {
      window.location = url;
      return;
    }

    // Run AJAX request.
    load(submit, url);
  };

  /**
   *
   */
  vbm.navigation.submit = function(url, data) {
    // AJAX request.
    vbm.ajax.call({
      url: url,
      type: 'POST',
      data: data,
      navigation: true,
      before_send: function(xhr, settings) {
        // Close any opened overlays.
        vbm.close_all_overlays();
        // Prepare container.
        $('#content').animate({opacity: 0.2}, 200);
      },
      success: function(response, status, xhr, wait) {
        // Restore opacity.
        if (!wait) {
          $('#content').stop(true, true).css('opacity', 1.0).show();
        }
      },
      commands: {
        set_content: function (contents) {
          vbm.commands.set_content(contents);
          vbm.scroll_top();
        }
      }
    });
  };

})(jQuery);
