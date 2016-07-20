$('.btnClaim').click(function(e) {
    var btn = this;
    var rating_id = $(this).parents('div.row').data('rating-id');
    $.post(CLAIM_URL, {check_claim: rating_id}, function(data) {
        if (data['claim_left']) {
            $('#btnOK').show();
            $('#claimLeft').html(data['text']).show();
            $('#btnCancel').hide();
            $('#requestDeletion').hide();
            $('#leaveClaim').hide();
        }
        else {
            var rating = $(btn).parents('div.row').find('span.rating').html();
            var comment = $(btn).parents('div.row').find('p.user-comment').html();
            var date = $(btn).parents('div.row').find('span.date').html();
            $('#chosenRating').html(rating);
            if (comment)
                $('#chosenComment').show().html(comment);
            else
                $('#chosenComment').hide().html('');
            $('#chosenDate').html(date);
            $('#btnOK').hide();
            $('#claimLeft').hide();
            $('#btnCancel').show();
            $('#leaveClaim').show();
            $('#requestDeletion').data('rating-id', rating_id).show();
        }
        $('#deletionClaimPopup').modal('show');
    });
});

$('#requestDeletion').click(function(e) {
    var id = $(this).data('rating-id');
    var reason = $('textarea[name="reason"]').val();
    if (!reason.trim()) {
        $('textarea[name="reason"]').parents('div.form-group').addClass('has-error');
        return;
    }
    $.post(CLAIM_URL, {rating_id: id, reason: reason});
    $('#deletionClaimPopup').modal('hide');
});

$('#deletionClaimPopup').on('hidden.bs.modal', function () {
    $('textarea[name="reason"]').val('').parents('div.form-group').removeClass('has-error');
});

$('.btn-question').click(function(e) {
    var btn = this;
    var rating_id = $(this).parents('div.row').data('rating-id');
    $.post(CHECK_QUESTION_URL, {check_question: rating_id}, function(data) {
        if (data['question_left']) {
            $('#btnOKQ').show();
            $('#questionLeft').html(data['text']).show();
            $('#btnCancelQ').hide();
            $('#requestQuestion').hide();
            $('#leaveQuestion').hide();
        }
        else {
            var rating = $(btn).parents('div.row').find('span.rating').html();
            var comment = $(btn).parents('div.row').find('p.user-comment').html();
            var date = $(btn).parents('div.row').find('span.date').html();
            $('#chosenRatingQ').html(rating);
            if (comment)
                $('#chosenCommentQ').show().html(comment);
            else
                $('#chosenCommentQ').hide().html('');
            $('#chosenDateQ').html(date);
            $('#btnOKQ').hide();
            $('#questionLeft').hide();
            $('#btnCancelQ').show();
            $('#leaveQuestion').show();
            $('#requestQuestion').data('rating-id', rating_id).show();
        }
        $('#sendQuestionPopup').modal('show');
    });
});

$('#requestQuestion').click(function(e) {
    var id = $(this).data('rating-id');
    var text = $('textarea[name="text-question"]').val();
    if (!text.trim()) {
        $('textarea[name="text-question"]').parents('div.form-group').addClass('has-error');
        return;
    }
    $.post(CHECK_QUESTION_URL, {rating_id: id, text: text});
    $('#sendQuestionPopup').modal('hide');
});

$('#sendQuestionPopup').on('hidden.bs.modal', function () {
    $('textarea[name="text-question"]').val('').parents('div.form-group').removeClass('has-error');
});
