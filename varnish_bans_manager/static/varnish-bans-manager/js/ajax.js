(function ($) {

  var ajaxers = [];

  vbm.ajax = vbm.ajax || {};

  $.ajaxSetup({
    cache: false,
    traditional: true
  });

  vbm.ajax.call = function(options) {
    // Init options.
    options.type = options.type || 'POST';
    options.context = options.context || $(document);
    options.element = options.element || null;
    options.navigation = options.navigation || false;
    options.data = options.data || {};
    options.commands = options.commands || {};
    options.before_send = options.before_send || null;
    options.success = options.success || null;
    options.error = options.error || null;

    // Do it!
    $.ajax({
      url: options.url,
      data: options.data,
      type: options.type,
      dataType: 'json',
      beforeSend: function(xhr, settings) {
        var result = true;
        xhr.vbm = {
          weight: 100
        };
        if (options.navigation) {
         xhr.setRequestHeader('X-Navigation', 1);
        }
        if (options.before_send) {
          result = options.before_send(xhr, settings);
        }
        if (result && options.element) {
         $(options.element).addClass('ajaxing');
        }
        return result;
      },
      complete: function(xhr, status) {
        if (options.element) {
         $(options.element).removeClass('ajaxing');
        }
      },
      success: function(response, status, xhr) {
        var wait = vbm.execute_commands(response, options.context, options.commands);
        if (options.success) {
          options.success(response, status, xhr, wait);
        }
      },
      error: function(xhr, status, error) {
        if (!xhr.aborted && (status != 'abort') && (status != 'aborted')) {
          vbm.notifications.notify('error', gettext("We are sorry, but the request couldn't be processed. Please, try again later."));
        }
        if (options.error) {
          options.error(xhr, status);
        }
      }
    });
  };

  $(document).ajaxSend(function(event, xhr, settings) {
    function same_origin(url) {
      // URL could be relative or scheme relative or absolute.
      var host = document.location.host; // host + port
      var protocol = document.location.protocol;
      var sr_origin = '//' + host;
      var origin = protocol + sr_origin;
      // Allow absolute or scheme relative URLs to same origin.
      return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
    }

    function safe_method(method) {
      return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    // Add/extend VBM stuff for xhr instance.
    var data = {
      id: vbm.serial++,
      weight: 100
    };
    $.extend(data, xhr.vbm || {});
    xhr.vbm = data;

    // Cancel any running ajaxers with equal or less weight.
    // Weight 0 is reserved for non-abortable ajaxers that can safely
    // run concurrently with any other request.
    for (var i=0; i < ajaxers.length; i++) {
      if ((ajaxers[i].vbm.weight > 0) && (ajaxers[i].vbm.weight <= xhr.vbm.weight)) {
        ajaxers[i].abort();
      }
    }

    // Update ajaxers list.
    ajaxers.push(xhr);

    // Add ajaxing body class.
    $('body').addClass('ajaxing');

    // Add CSRF header (see https://docs.djangoproject.com/en/1.2/ref/contrib/csrf/#ajax).
    if (!safe_method(settings.type) && same_origin(settings.url)) {
      xhr.setRequestHeader("X-CSRFToken", vbm.csrf_token);
    }
  });

  $(document).ajaxComplete(function(event, xhr, settings) {
    // Update ajaxers list.
    for (var i=0; i < ajaxers.length; i++) {
      if (ajaxers[i].vbm.id === xhr.vbm.id) {
        ajaxers.splice(i, 1);
        break;
      }
    }

    // Remove ajaxing body class?
    if (ajaxers.length === 0) {
      $('body').removeClass('ajaxing');
    }
  });

})(jQuery);
