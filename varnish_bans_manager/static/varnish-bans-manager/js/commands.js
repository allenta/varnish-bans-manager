(function ($) {

  vbm.commands = vbm.commands || {};

  /******************************************************************************
   * UPDATE PAGE ID.
   ******************************************************************************/

  vbm.commands.update_page_id = function(page_id) {
    $('body').removeClass(vbm.page_id + '-page');
    vbm.page_id = page_id;
    $('body').addClass(vbm.page_id + '-page');
  };

  /******************************************************************************
   * CHECK VERSION.
   ******************************************************************************/

  vbm.commands.check_version = function(version) {
    if ((version.js.major != vbm.version.js.major) || (version.css.major != vbm.version.css.major)) {
      window.location.reload();
      return true;
    }
  };

  /******************************************************************************
   * NAVIGATE.
   ******************************************************************************/

  vbm.commands.navigate = function(url) {
    vbm.navigation.navigate(url);
    return true;
  };

  /******************************************************************************
   * REDIRECT.
   ******************************************************************************/

  vbm.commands.redirect = function(url) {
    window.location = url;
    return true;
  };

  /******************************************************************************
   * DOWNLOAD.
   ******************************************************************************/

  vbm.commands.downlad = function(url) {
    window.location = url;
  };

  /******************************************************************************
   * SET CONTENT.
   ******************************************************************************/

  vbm.commands.set_content = function(contents) {
    // Detach behaviors.
    vbm.detach_behaviors('#content');

    // Update container.
    $('#content').html(contents);

    // Attach behaviors.
    vbm.attach_behaviors('#content');
  };

  /******************************************************************************
   * ALERT.
   ******************************************************************************/

  vbm.commands.alert = function(message) {
    alert(message);
  };

  /******************************************************************************
   * MODAL & CLOSE_MODAL.
   ******************************************************************************/

  vbm.commands.modal = function(contents) {
    // Append any included script tags to the document so they get
    // executed.
    $(contents).filter('script').appendTo('body');
    // Sanity check: Modal contents must consist of a single
    // element with the class modal.
    var modal = $(contents).filter('.modal');
    if (modal.length == 1) {
      vbm.modal.open(modal);
    }
  };

  vbm.commands.close_modal = function() {
    vbm.modal.close_all();
  };

  /******************************************************************************
   * NOTIFY.
   ******************************************************************************/

  vbm.commands.notify = function(messages) {
    if (messages.length > 0) {
      // Find and clean up target 'inline-notifications-container' DOM element (if any).
      var container = $('.inline-notifications-container').last();
      if ($(container).length > 0) {
        $(container).html('');
      }
      // Render each message.
      for (var i = 0; i < messages.length; i++) {
        // Inline notifications.
        if ((messages[i].tags.indexOf('inline') != -1) && ($(container).length > 0)) {
          vbm.notifications.notify(messages[i].type, messages[i].message, null, container);
        }
        // Cool & floating notifications.
        else {
          var expires = null;
          if ((messages[i].type != 'error')) {
            expires = 5000 + 100 * messages[i].message.length;
          }
          vbm.notifications.notify(messages[i].type, messages[i].message, expires, (messages.length > 1) ? 'floating' : 'cool');
        }
      }
    }
  };

  /******************************************************************************
   * DEBUG.
   ******************************************************************************/

  vbm.commands.debug = function(report) {
    var wrapper = $('#debug-toolbar .log');
    vbm.detach_behaviors(wrapper);
    wrapper.html(report);
    vbm.attach_behaviors(wrapper);
  };

  vbm.commands.timer = function(time) {
    $('#debug-toolbar .execution-time').html(time);
  };

})(jQuery);


/******************************************************************************
 * PROGRESS.
 ******************************************************************************/

(function ($) {

  var next_ping_timer = null;
  var next_increment_timer = null;

  function enqueue_next_ping(url, timeout) {
    next_ping_timer = setTimeout(function() {
      vbm.ajax.call({
        type: 'GET',
        url: url,
        error: function(xhr, status) {
          enqueue_next_ping(url, timeout);
        }
      });
    }, timeout);
  }

  function enqueue_next_increment(bar, n, inc, timeout) {
    if (n > 0) {
      next_increment_timer = setTimeout(function() {
        var value = parseFloat($(bar).attr('data-value')) + inc;
        if (value <= (bar).attr('data-max')) {
          $(bar).attr('data-value', value).css('width', value + '%');
          enqueue_next_increment(bar, n-1, inc, timeout);
        }
      }, timeout);
    }
  }

  vbm.commands.show_progress = function(progress_url, cancel_url, timeout, title) {
    // Build progress modal.
    var modal = $(
      '<div class="modal hide fade" id="progress-modal" data-url="' + progress_url + '">' +
      '  <div class="modal-header">' +
      '    <h3>' + title + '</h3>' +
      '  </div>' +
      '  <div class="modal-body">' +
      '    <div class="progress progress-striped active" style="display: none;">' +
      '      <div class="bar" data-max="0" data-value="0" style="width: 0%;"></div>' +
      '    </div>' +
      '    <p class="pull-right"><i class="font-awesome font-awesome-warning-sign"></i> ' + gettext('Please, be patient. <strong>Do not close or reload the page!</strong>') + '</p>' +
      '  </div>' +
      '  <div class="modal-footer">' +
      '    <a href="#" class="btn btn-danger"><i class="icon-remove icon-white"></i> ' + gettext('Abort') + '</a>' +
      '  </div>' +
      '</div>');
    // Bind cancel button event.
    $('.modal-footer .btn', modal).click(function() {
      clearInterval(next_ping_timer);
      clearInterval(next_increment_timer);
      vbm.ajax.call({
        url: cancel_url,
        type: 'POST',
        element: this
      });
      return false;
    });
    // Open progress modal.
    vbm.modal.open(modal);
    // Enqueue next progress update.
    enqueue_next_ping(progress_url, timeout);
  };

  vbm.commands.update_progress = function(value, timeout) {
    // Fetch progress modal.
    modal = $('#progress-modal');
    if (modal.length > 0) {
      // Update value (if any)
      if (value) {
        // Display progress bar.
        $(modal).find('.progress').show();
        // Render small increments every 100ms until next expected ping.
        var bar = $(modal).find('.bar');
        var diff = value - $(bar).attr('data-max');
        if (diff > 0) {
          $(bar).attr('data-max', value);
          var nupdates = Math.ceil(timeout/100);
          enqueue_next_increment(bar, nupdates, diff/nupdates, 100);
        }
      }
      // Enqueue next progress update.
      enqueue_next_ping($(modal).attr('data-url'), timeout);
    }
  };

  vbm.commands.hide_progress = function() {
    modal = $('#progress-modal');
    if (modal.length > 0) {
      $(modal).modal('hide');
    }
  };
})(jQuery);
