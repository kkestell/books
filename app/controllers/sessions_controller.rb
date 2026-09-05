class SessionsController < ApplicationController
  allow_unauthenticated_access only: %i[new create]

  def new
    redirect_to root_path if current_user
  end

  def create
    user = User.find_by(username: params[:username])

    if user
      log_in(user)
      redirect_to root_path
    else
      redirect_to login_path, alert: "Choose a user to log in as."
    end
  end

  def destroy
    log_out
    redirect_to login_path
  end
end
