(function ($) {

  var floating_notifications = [];

  vbm.notifications = vbm.notifications || {};

  /**
   *   type: 'status' | 'warning' | 'error'.
   *   container: 'cool' (default) | 'floating' | 'inline'
   */
  vbm.notifications.notify = function(type, text, expires, container) {
    container = (typeof(container) != 'undefined') ? container : 'cool';
    if ((container == 'cool') || (container == 'floating')) {
      vbm.notifications[container](type, text, expires);
    }
    else {
      vbm.notifications.inline(type, text, expires, container);
    }
  };

  /**
   *
   */
  vbm.notifications.inline = function(type, text, expires, container) {
    // Build & insert new notification element.
    var element = $('<div class="notification inline-notification ' + type + '"><a class="close" href="#">&times;</a><p>' + text + '</p></div>');
    $(container).append(element);
    vbm.attach_behaviors(element);

    // Add expiration timeout.
    if (expires) {
      setTimeout(function() { $('a.close', element).click(); }, expires);
    }

    // Register element close event.
    $('a.close', element).click(function() {
      $(this).parent().slideUp('fast', function() { $(this).remove(); });
      return false;
    });
  };

  /**
   *
   */
  vbm.notifications.floating = function(type, text, expires) {
    var placeholders = {
      type: type,
      text: text
    };
    var notification = $('#floating-notifications-container').notify('create', 'default-template', placeholders, {
      expires: (typeof(expires) != 'undefined') ? expires : 7000,
      click: function(event, instance) {
        if (event.metaKey) {
          vbm.notifications.close_all();
        }
      }
    });
    vbm.attach_behaviors(notification.element);
    floating_notifications.push(notification);
  };

  /**
   *
   */
  vbm.notifications.cool = function(type, text, expires) {
    // Cool notifications cannot be stacked => clean up previous notification.
    $('#overlay .cool-notification').remove();

    // Build & insert new notification element.
    var element = $('<div class="' + type + ' notification cool-notification"><p>' + text + '</p></div>');
    $('#overlay').append(element);
    vbm.attach_behaviors(element);
    $(element).css('bottom', -$(element).outerHeight()).animate({bottom: '0'}, 500);

    // Add expiration timeout.
    if (expires) {
      setTimeout(function() { $(element).click(); }, expires);
    }

    // Register element close event.
    $(element).click(function() {
      $(this).animate({bottom: -$(this).outerHeight()}, 500, 'linear', function() { $(this).remove(); });
    });
  };

  /**
   *
   */
  vbm.notifications.close_all = function() {
    // Close floating notifications.
    for (var i = 0; i < floating_notifications.length; i++) {
      floating_notifications[i].close();
    }
    floating_notifications = [];

    // Close cool notifications.
    $('#overlay .cool-notification').click();

    // Close inline notifications.
    $('.inline-notifications-container .inline-notification .close').click();
  };

})(jQuery);
